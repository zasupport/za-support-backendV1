from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import json
import logging

from app.database import get_db, SessionLocal
from app.models import ChatSession, ChatMessage, User, ChatSessionStatus, MessageType, UserRole
from app.schemas import ChatSessionCreate, ChatSessionOut, ChatMessageCreate, ChatMessageOut
from app.auth import get_current_user
from app.config import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# --- WebSocket connection manager ---

class ConnectionManager:
    def __init__(self):
        # session_id -> list of websocket connections
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: int, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)


manager = ConnectionManager()


def _authenticate_ws_token(token: str, db) -> Optional[User]:
    """Validate a JWT token and return the user, or None if invalid."""
    from jose import JWTError, jwt as jose_jwt

    try:
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        user_id = int(sub)
    except (JWTError, ValueError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    return user


# --- REST endpoints ---

@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ChatSession(
        ticket_id=data.ticket_id,
        user_id=current_user.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Auto-create a system message
    system_msg = ChatMessage(
        session_id=session.id,
        sender_id=current_user.id,
        content=f"Chat session started by {current_user.username}",
        message_type=MessageType.system,
    )
    db.add(system_msg)
    db.commit()

    return session


@router.get("/sessions", response_model=list[ChatSessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ChatSession)

    if current_user.role == UserRole.customer:
        query = query.filter(ChatSession.user_id == current_user.id)

    return query.order_by(ChatSession.created_at.desc()).all()


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if current_user.role == UserRole.customer and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return session


@router.post("/sessions/{session_id}/join")
def join_session_as_agent(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.agent, UserRole.admin):
        raise HTTPException(status_code=403, detail="Only agents can join sessions")

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    session.agent_id = current_user.id
    db.commit()
    db.refresh(session)
    return {"status": "joined", "session_id": session.id, "agent": current_user.username}


@router.post("/sessions/{session_id}/close")
def close_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if current_user.role == UserRole.customer and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.status = ChatSessionStatus.closed
    session.closed_at = datetime.utcnow()

    # Add system close message
    close_msg = ChatMessage(
        session_id=session.id,
        sender_id=current_user.id,
        content=f"Chat session closed by {current_user.username}",
        message_type=MessageType.system,
    )
    db.add(close_msg)
    db.commit()

    return {"status": "closed", "session_id": session.id}


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if current_user.role == UserRole.customer and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Mark unread messages as read for current user
    db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.sender_id != current_user.id,
        ChatMessage.is_read == False,
    ).update({"is_read": True})
    db.commit()

    return session.messages


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    session_id: int,
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if session.status == ChatSessionStatus.closed:
        raise HTTPException(status_code=400, detail="Chat session is closed")

    if current_user.role == UserRole.customer and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    message = ChatMessage(
        session_id=session_id,
        sender_id=current_user.id,
        content=data.content,
        message_type=data.message_type,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


# --- WebSocket endpoint for real-time chat ---

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: int, token: str = Query(...)):
    db = SessionLocal()
    try:
        # Authenticate via JWT token query param
        user = _authenticate_ws_token(token, db)
        if not user:
            await websocket.close(code=4001)
            return

        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session or session.status == ChatSessionStatus.closed:
            await websocket.close(code=4004)
            return

        # Verify user has access to this session
        if user.role == UserRole.customer and session.user_id != user.id:
            await websocket.close(code=4003)
            return

        await manager.connect(websocket, session_id)
        logger.info(f"WebSocket connected: user {user.id} to session {session_id}")

        try:
            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)

                content = data.get("content", "")
                if not content:
                    await websocket.send_json({"error": "content is required"})
                    continue

                # Always use the authenticated user's ID as sender
                message = ChatMessage(
                    session_id=session_id,
                    sender_id=user.id,
                    content=content,
                    message_type=MessageType.text,
                )
                db.add(message)
                db.commit()
                db.refresh(message)

                # Broadcast to all connections in the session
                await manager.broadcast_to_session(session_id, {
                    "id": message.id,
                    "session_id": session_id,
                    "sender_id": message.sender_id,
                    "content": message.content,
                    "message_type": message.message_type.value,
                    "created_at": message.created_at.isoformat(),
                })

        except WebSocketDisconnect:
            manager.disconnect(websocket, session_id)
            logger.info(f"WebSocket disconnected: user {user.id} from session {session_id}")
    finally:
        db.close()
