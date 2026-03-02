#!/usr/bin/env python3
"""
ZA Support — Diagnostic Build Agent v3.0
Runs on macOS/Linux endpoints and communicates with the ZA Support Backend.

Features:
  - Heartbeat registration on startup and interval
  - System data collection (CPU, memory, disk, battery, security)
  - Uploads collection data to the backend
  - Polls for and executes remote commands
  - Reports command results back to the backend

Usage:
    python3 agent.py --server http://localhost:8080 --serial MY-MAC-001
    python3 agent.py --server https://your-render-url.onrender.com --serial OFFICE-MAC-01

Environment variables (override CLI args):
    ZA_SERVER_URL       Backend server URL
    ZA_DEVICE_SERIAL    Device serial number
"""

import argparse
import json
import logging
import os
import platform
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

__version__ = "3.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("za-agent")


# ===================================================================
# System Data Collectors
# ===================================================================

def get_cpu_usage() -> float:
    """Get CPU usage percentage. Works on macOS and Linux."""
    try:
        if platform.system() == "Darwin":
            out = subprocess.check_output(
                ["ps", "-A", "-o", "%cpu"], text=True, timeout=10
            )
            lines = out.strip().split("\n")[1:]  # skip header
            total = sum(float(l.strip()) for l in lines if l.strip())
            # Normalize by CPU count
            cpu_count = os.cpu_count() or 1
            return min(round(total / cpu_count, 1), 100.0)
        else:
            # Linux: read /proc/stat
            with open("/proc/stat") as f:
                line = f.readline()
            parts = line.split()
            idle = int(parts[4])
            total = sum(int(p) for p in parts[1:])
            # Single snapshot — rough estimate
            usage = 100.0 * (1 - idle / total) if total > 0 else 0
            return round(usage, 1)
    except Exception as e:
        logger.warning(f"CPU check failed: {e}")
        return 0.0


def get_memory_info() -> dict:
    """Get memory usage percentage."""
    try:
        if platform.system() == "Darwin":
            out = subprocess.check_output(
                ["vm_stat"], text=True, timeout=10
            )
            pages = {}
            for line in out.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    val = val.strip().rstrip(".")
                    try:
                        pages[key.strip()] = int(val)
                    except ValueError:
                        pass
            page_size = 16384  # default on Apple Silicon; 4096 on Intel
            try:
                ps_out = subprocess.check_output(
                    ["sysctl", "-n", "hw.pagesize"], text=True, timeout=5
                )
                page_size = int(ps_out.strip())
            except Exception:
                pass
            free = pages.get("Pages free", 0) * page_size
            active = pages.get("Pages active", 0) * page_size
            inactive = pages.get("Pages inactive", 0) * page_size
            wired = pages.get("Pages wired down", 0) * page_size
            total = free + active + inactive + wired
            used = active + wired
            pressure = round(100 * used / total, 1) if total > 0 else 0
            return {"pressure_pct": pressure, "total_gb": round(total / 1e9, 1)}
        else:
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = int(parts[1].strip().split()[0])
            total = meminfo.get("MemTotal", 1)
            available = meminfo.get("MemAvailable", 0)
            pressure = round(100 * (1 - available / total), 1)
            return {"pressure_pct": pressure, "total_gb": round(total / 1e6, 1)}
    except Exception as e:
        logger.warning(f"Memory check failed: {e}")
        return {"pressure_pct": 0, "total_gb": 0}


def get_disk_info() -> dict:
    """Get root disk usage."""
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used_pct = round(100 * (1 - free / total), 1) if total > 0 else 0
        return {
            "used_pct": used_pct,
            "total_gb": round(total / 1e9, 1),
            "free_gb": round(free / 1e9, 1),
        }
    except Exception as e:
        logger.warning(f"Disk check failed: {e}")
        return {"used_pct": 0, "total_gb": 0, "free_gb": 0}


def get_battery_info() -> dict:
    """Get battery percentage (macOS only; returns 100 on desktop/Linux)."""
    try:
        if platform.system() == "Darwin":
            out = subprocess.check_output(
                ["pmset", "-g", "batt"], text=True, timeout=10
            )
            for line in out.split("\n"):
                if "%" in line:
                    # Example: "-InternalBattery-0 (id=...)  85%; charging;"
                    pct_str = line.split("%")[0].split()[-1]
                    return {"percentage": int(pct_str)}
            return {"percentage": 100}  # Desktop Mac — no battery
        elif os.path.exists("/sys/class/power_supply/BAT0/capacity"):
            with open("/sys/class/power_supply/BAT0/capacity") as f:
                return {"percentage": int(f.read().strip())}
        else:
            return {"percentage": 100}  # Desktop Linux
    except Exception as e:
        logger.warning(f"Battery check failed: {e}")
        return {"percentage": 100}


def get_security_info() -> dict:
    """Get basic security status."""
    result = {"firewall": "unknown", "filevault": "unknown"}
    try:
        if platform.system() == "Darwin":
            # Firewall
            try:
                fw = subprocess.check_output(
                    ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                    text=True, timeout=10, stderr=subprocess.DEVNULL,
                )
                result["firewall"] = "enabled" if "enabled" in fw.lower() else "disabled"
            except Exception:
                result["firewall"] = "unknown"
            # FileVault
            try:
                fv = subprocess.check_output(
                    ["fdesetup", "status"], text=True, timeout=10, stderr=subprocess.DEVNULL,
                )
                result["filevault"] = "on" if "on" in fv.lower() else "off"
            except Exception:
                result["filevault"] = "unknown"
        else:
            # Linux — check ufw
            try:
                ufw = subprocess.check_output(
                    ["ufw", "status"], text=True, timeout=10, stderr=subprocess.DEVNULL,
                )
                result["firewall"] = "enabled" if "active" in ufw.lower() else "disabled"
            except Exception:
                result["firewall"] = "unknown"
            # Linux encryption — check LUKS
            try:
                lsblk = subprocess.check_output(
                    ["lsblk", "-o", "TYPE"], text=True, timeout=10, stderr=subprocess.DEVNULL,
                )
                result["filevault"] = "on" if "crypt" in lsblk else "off"
            except Exception:
                result["filevault"] = "unknown"
    except Exception as e:
        logger.warning(f"Security check failed: {e}")
    return result


def get_network_info() -> dict:
    """Get basic network info."""
    try:
        hostname = socket.gethostname()
        return {"hostname": hostname}
    except Exception:
        return {}


def get_uptime() -> int:
    """Get system uptime in seconds."""
    try:
        if platform.system() == "Darwin":
            out = subprocess.check_output(
                ["sysctl", "-n", "kern.boottime"], text=True, timeout=5
            )
            # Format: "{ sec = 1709366400, usec = 0 } ..."
            sec_str = out.split("sec = ")[1].split(",")[0]
            boot_time = int(sec_str)
            return int(time.time() - boot_time)
        elif os.path.exists("/proc/uptime"):
            with open("/proc/uptime") as f:
                return int(float(f.read().split()[0]))
    except Exception:
        pass
    return 0


def get_top_processes(n: int = 5) -> list:
    """Get top N processes by CPU usage."""
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,pcpu,pmem,comm", "-r"],
            text=True, timeout=10,
        )
        procs = []
        for line in out.strip().split("\n")[1:n + 1]:
            parts = line.split(None, 3)
            if len(parts) >= 4:
                procs.append({
                    "pid": int(parts[0]),
                    "cpu": float(parts[1]),
                    "mem": float(parts[2]),
                    "name": parts[3],
                })
        return procs
    except Exception:
        return []


# ===================================================================
# API Client
# ===================================================================

class AgentClient:
    """Communicates with the ZA Support Backend API."""

    def __init__(self, server_url: str, serial: str):
        self.server = server_url.rstrip("/")
        self.serial = serial
        self.collection_interval = 300
        self.heartbeat_interval = 60
        self.command_poll_interval = 60

    def _post(self, path: str, data: dict) -> dict:
        url = f"{self.server}{path}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            logger.error(f"POST {path} → {e.code}: {body}")
            return {"error": e.code, "detail": body}
        except Exception as e:
            logger.error(f"POST {path} failed: {e}")
            return {"error": str(e)}

    def _get(self, path: str) -> dict:
        url = f"{self.server}{path}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            logger.error(f"GET {path} → {e.code}: {body}")
            return {"error": e.code}
        except Exception as e:
            logger.error(f"GET {path} failed: {e}")
            return {"error": str(e)}

    def heartbeat(self) -> dict:
        data = {
            "serial": self.serial,
            "model": platform.machine() + " " + platform.node(),
            "hostname": socket.gethostname(),
            "os_version": platform.platform(),
            "agent_version": __version__,
            "hardware_uuid": self._get_hardware_uuid(),
            "uptime_seconds": get_uptime(),
        }
        resp = self._post("/api/v1/agent/heartbeat", data)
        if "error" not in resp:
            self.collection_interval = resp.get("collection_interval", self.collection_interval)
            self.heartbeat_interval = resp.get("heartbeat_interval", self.heartbeat_interval)
            self.command_poll_interval = resp.get("command_poll_interval", self.command_poll_interval)
            logger.info(
                f"Heartbeat OK — pending={resp.get('pending_commands', 0)} "
                f"ci={self.collection_interval}s hi={self.heartbeat_interval}s"
            )
        return resp

    def collect_and_upload(self, collection_type: str = "lite") -> dict:
        logger.info(f"Collecting {collection_type} data...")
        data = {
            "agent_version": __version__,
            "collection_type": collection_type,
            "timestamp": datetime.utcnow().isoformat(),
            "device": {"serial": self.serial, "model": platform.machine()},
            "battery": get_battery_info(),
            "storage": get_disk_info(),
            "memory": get_memory_info(),
            "cpu": {"usage_pct": get_cpu_usage()},
            "security": get_security_info(),
            "network": get_network_info(),
            "errors": {},
            "uptime_seconds": get_uptime(),
            "top_processes": get_top_processes(),
        }
        resp = self._post("/api/v1/agent/upload", data)
        if "error" not in resp:
            alerts = resp.get("alerts", [])
            if alerts:
                logger.warning(f"Server alerts: {json.dumps(alerts, indent=2)}")
            else:
                logger.info("Collection uploaded — no alerts")
        return resp

    def poll_commands(self) -> list:
        resp = self._get(f"/api/v1/agent/commands/{self.serial}")
        if isinstance(resp, list) and resp:
            logger.info(f"Received {len(resp)} command(s)")
            return resp
        return []

    def execute_command(self, cmd: dict) -> None:
        cmd_id = cmd.get("id", "unknown")
        cmd_type = cmd.get("type", "")
        payload = cmd.get("payload", "")
        logger.info(f"Executing command {cmd_id}: {cmd_type}")

        start = time.time()
        result_text = ""
        status = "success"

        try:
            if cmd_type == "collect_lite":
                self.collect_and_upload("lite")
                result_text = "Lite collection completed"
            elif cmd_type == "collect_full":
                self.collect_and_upload("full")
                result_text = "Full collection completed"
            elif cmd_type == "get_process_list":
                out = subprocess.check_output(["ps", "aux"], text=True, timeout=15)
                result_text = out[:5000]
            elif cmd_type == "get_disk_usage":
                out = subprocess.check_output(["df", "-h"], text=True, timeout=10)
                result_text = out
            elif cmd_type == "get_network_info":
                out = subprocess.check_output(["ifconfig" if platform.system() == "Darwin" else "ip", "addr"], text=True, timeout=10)
                result_text = out[:5000]
            elif cmd_type == "get_battery_detail":
                if platform.system() == "Darwin":
                    out = subprocess.check_output(["system_profiler", "SPPowerDataType"], text=True, timeout=15)
                    result_text = out[:5000]
                else:
                    result_text = json.dumps(get_battery_info())
            elif cmd_type == "get_system_log":
                if platform.system() == "Darwin":
                    out = subprocess.check_output(["log", "show", "--last", "5m", "--style", "compact"], text=True, timeout=30)
                    result_text = out[-5000:]  # last 5000 chars
                else:
                    out = subprocess.check_output(["journalctl", "-n", "100", "--no-pager"], text=True, timeout=15)
                    result_text = out[-5000:]
            elif cmd_type == "get_installed_apps":
                if platform.system() == "Darwin":
                    out = subprocess.check_output(["ls", "/Applications"], text=True, timeout=10)
                    result_text = out
                else:
                    out = subprocess.check_output(["dpkg", "-l"], text=True, timeout=15)
                    result_text = out[:5000]
            elif cmd_type == "get_security_status":
                result_text = json.dumps(get_security_info(), indent=2)
            elif cmd_type == "get_wifi_diagnostics":
                if platform.system() == "Darwin":
                    out = subprocess.check_output(
                        ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                        text=True, timeout=10,
                    )
                    result_text = out
                else:
                    out = subprocess.check_output(["iwconfig"], text=True, timeout=10, stderr=subprocess.DEVNULL)
                    result_text = out
            elif cmd_type == "get_login_items":
                if platform.system() == "Darwin":
                    out = subprocess.check_output(["osascript", "-e", 'tell application "System Events" to get the name of every login item'], text=True, timeout=10)
                    result_text = out
                else:
                    result_text = "Not supported on Linux"
            elif cmd_type == "get_thermal_info":
                if platform.system() == "Darwin":
                    result_text = "Thermal monitoring requires IOKit (not available via CLI)"
                else:
                    try:
                        out = subprocess.check_output(["sensors"], text=True, timeout=10)
                        result_text = out
                    except Exception:
                        result_text = "lm-sensors not installed"
            elif cmd_type == "get_agent_status":
                result_text = json.dumps({
                    "agent_version": __version__,
                    "serial": self.serial,
                    "platform": platform.platform(),
                    "uptime": get_uptime(),
                    "collection_interval": self.collection_interval,
                    "heartbeat_interval": self.heartbeat_interval,
                })
            elif cmd_type == "run_safe_command":
                # Only allow read-only safe commands
                SAFE_PREFIXES = ["ls", "cat", "df", "ps", "uptime", "whoami", "hostname", "uname", "sw_vers", "sysctl"]
                if payload and any(payload.strip().startswith(p) for p in SAFE_PREFIXES):
                    out = subprocess.check_output(payload, shell=True, text=True, timeout=30, stderr=subprocess.STDOUT)
                    result_text = out[:5000]
                else:
                    status = "rejected"
                    result_text = f"Command not in safe list: {payload}"
            elif cmd_type == "set_collection_interval":
                try:
                    interval = int(payload)
                    if interval >= 60:
                        self.collection_interval = interval
                        result_text = f"Collection interval set to {interval}s"
                    else:
                        status = "error"
                        result_text = "Minimum interval is 60s"
                except ValueError:
                    status = "error"
                    result_text = f"Invalid interval: {payload}"
            else:
                status = "unsupported"
                result_text = f"Unknown command type: {cmd_type}"
        except subprocess.TimeoutExpired:
            status = "timeout"
            result_text = "Command timed out"
        except Exception as e:
            status = "error"
            result_text = str(e)

        duration = int(time.time() - start)
        self._post("/api/v1/agent/command-result", {
            "command_id": cmd_id,
            "serial": self.serial,
            "status": status,
            "result": result_text,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"Command {cmd_id} completed: {status} ({duration}s)")

    def _get_hardware_uuid(self) -> str:
        try:
            if platform.system() == "Darwin":
                out = subprocess.check_output(
                    ["system_profiler", "SPHardwareDataType"],
                    text=True, timeout=10,
                )
                for line in out.split("\n"):
                    if "Hardware UUID" in line or "Provisioning UDID" in line:
                        return line.split(":")[-1].strip()
            elif os.path.exists("/etc/machine-id"):
                with open("/etc/machine-id") as f:
                    return f.read().strip()
        except Exception:
            pass
        return f"generated-{socket.gethostname()}-{platform.machine()}"


# ===================================================================
# Main Run Loop
# ===================================================================

def run_agent(server_url: str, serial: str):
    client = AgentClient(server_url, serial)
    logger.info(f"ZA Diagnostic Agent v{__version__} starting")
    logger.info(f"  Server:  {server_url}")
    logger.info(f"  Serial:  {serial}")
    logger.info(f"  Host:    {socket.gethostname()}")
    logger.info(f"  OS:      {platform.platform()}")

    # Graceful shutdown
    running = True

    def shutdown(sig, frame):
        nonlocal running
        logger.info(f"Received signal {sig} — shutting down")
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Initial heartbeat + collection
    client.heartbeat()
    client.collect_and_upload("lite")

    last_heartbeat = time.time()
    last_collection = time.time()
    last_poll = time.time()

    while running:
        now = time.time()

        # Heartbeat
        if now - last_heartbeat >= client.heartbeat_interval:
            client.heartbeat()
            last_heartbeat = now

        # Collection
        if now - last_collection >= client.collection_interval:
            client.collect_and_upload("lite")
            last_collection = now

        # Command polling
        if now - last_poll >= client.command_poll_interval:
            commands = client.poll_commands()
            for cmd in commands:
                if not running:
                    break
                client.execute_command(cmd)
            last_poll = now

        # Sleep 1s between loop iterations
        time.sleep(1)

    logger.info("Agent stopped")


def main():
    parser = argparse.ArgumentParser(description="ZA Support Diagnostic Agent v3.0")
    parser.add_argument(
        "--server", default=os.environ.get("ZA_SERVER_URL", "http://localhost:8080"),
        help="Backend server URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--serial", default=os.environ.get("ZA_DEVICE_SERIAL", f"{socket.gethostname()}-{platform.machine()}"),
        help="Device serial number (default: hostname-arch)",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run a single heartbeat + collection and exit (no loop)",
    )
    args = parser.parse_args()

    if args.once:
        client = AgentClient(args.server, args.serial)
        logger.info(f"ZA Diagnostic Agent v{__version__} — single run")
        logger.info(f"  Server: {args.server}")
        logger.info(f"  Serial: {args.serial}")
        resp = client.heartbeat()
        print(json.dumps(resp, indent=2))
        resp = client.collect_and_upload("lite")
        print(json.dumps(resp, indent=2))
    else:
        run_agent(args.server, args.serial)


if __name__ == "__main__":
    main()
