# Health Check Scout — Mac Agent App

Health Check Scout is the macOS agent that runs on client devices, reporting telemetry every 60 seconds and uploading full diagnostics on demand.

## Architecture

```
┌──────────────────┐        HTTPS/Bearer        ┌────────────────────────┐
│  Health Check     │ ──────────────────────────▶ │  ZA Support Backend    │
│  Scout (macOS)   │   60s heartbeat + diag      │  api.zasupport.com     │
└──────────────────┘                              └────────────────────────┘
```

## Agent Configuration

The agent reads from `settings.conf` on each Mac:

```ini
# /usr/local/zasupport/settings.conf
BACKEND_URL=https://api.zasupport.com
AGENT_TOKEN=<token-from-render-dashboard>
CLIENT_ID=<client-identifier>
HEARTBEAT_INTERVAL=60
```

### Environment Variables (Backend Side)

| Variable | Purpose | Where Set |
|----------|---------|-----------|
| `AGENT_AUTH_TOKEN` | Current bearer token agents authenticate with | Render Dashboard |
| `AGENT_AUTH_TOKEN_OLD` | Previous token (grace period during rotation) | Render Dashboard |

## API Endpoints Used by Scout

All under `https://api.zasupport.com/api/v1/agent/`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/health` | None | Agent pre-flight connectivity check |
| `POST` | `/heartbeat` | Bearer | 60-second telemetry (CPU, memory, disk, battery, security) |
| `POST` | `/diagnostics` | Bearer | Full `za_diag_v3.sh` JSON upload |
| `GET` | `/devices` | Bearer | List all reporting devices |
| `GET` | `/devices/{serial}` | Bearer | Single device status lookup |

## Heartbeat Payload

```json
{
  "serial": "C02XL0ABCD",
  "hostname": "evans-macbook",
  "client_id": "DR_SHOUL",
  "cpu_load": 34.2,
  "memory_pressure": 67.8,
  "disk_used_pct": 71.0,
  "battery": 85.0,
  "security": {
    "sip_enabled": true,
    "filevault_on": true,
    "firewall_on": true,
    "gatekeeper_on": true
  }
}
```

## Diagnostic Upload Payload

Full JSON output from `za_diag_v3.sh`:

```json
{
  "serial": "C02XL0ABCD",
  "hostname": "evans-macbook",
  "client_id": "DR_SHOUL",
  "payload": { /* complete za_diag_v3.sh JSON — 215 data points */ }
}
```

## Token Rotation (Zero Downtime)

1. **Render Dashboard**: Copy current `AGENT_AUTH_TOKEN` → new env var `AGENT_AUTH_TOKEN_OLD`
2. **Render Dashboard**: Set `AGENT_AUTH_TOKEN` to a new value:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. Service redeploys — **both tokens now accepted**
4. Update each Mac's `settings.conf` with new token (no rush)
5. Delete `AGENT_AUTH_TOKEN_OLD` once all agents are confirmed working

## Custom Domain Setup (URL Stability)

To ensure agents never break if the Render service is renamed:

1. Render Dashboard → Settings → Custom Domains → Add `api.zasupport.com`
2. DNS registrar → CNAME: `api.zasupport.com` → Render target
3. Render auto-provisions TLS
4. Verify: `curl -s https://api.zasupport.com/api/v1/agent/health`
5. Update all agent `settings.conf` to use `https://api.zasupport.com`

## Device Status Logic

- **Online**: Last heartbeat within 120 seconds
- **Offline**: No heartbeat for 120+ seconds
- **Stale**: No heartbeat for 24+ hours (triggers automation event)

## Data Flow

```
Scout Agent (Mac)
  ├── Every 60s → POST /heartbeat → agent_heartbeats table (TimescaleDB)
  │                                  └── 15-min continuous aggregate
  │                                  └── 90-day auto-retention
  └── On demand → POST /diagnostics → diagnostic_reports table (JSONB + GIN index)
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| 401 on heartbeat | Token mismatch — verify `AGENT_TOKEN` in settings.conf matches `AGENT_AUTH_TOKEN` on Render |
| Connection refused | Backend URL wrong or service down — check `curl https://api.zasupport.com/api/v1/agent/health` |
| 500 on heartbeat | `AGENT_AUTH_TOKEN` env var not set on Render |
| Heartbeats arriving but device shows offline | Clock skew or `ONLINE_THRESHOLD_SECONDS` too low (default 120s) |

## Current Clients

| Client | ISP | Notes |
|--------|-----|-------|
| Dr Evan Shoul | Stem (X-DSL underlying) | Gateway 192.168.1.252 |
| Charles Chemel | NTT Data | UniFi Site Manager |
