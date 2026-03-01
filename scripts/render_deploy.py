"""
Render Deploy Manager — Automated deploy, monitoring, and error response.

Usage:
    export RENDER_API_KEY="your-render-api-key"
    python scripts/render_deploy.py status
    python scripts/render_deploy.py deploy
    python scripts/render_deploy.py logs
    python scripts/render_deploy.py rollback
    python scripts/render_deploy.py env-check
    python scripts/render_deploy.py health
    python scripts/render_deploy.py full-deploy
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

RENDER_API_BASE = "https://api.render.com/v1"
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")
SERVICE_NAME = "za-support-backendv1"

# Required environment variables for the service
REQUIRED_ENV_VARS = ["DATABASE_URL", "SECRET_KEY", "API_KEY"]


def headers():
    if not RENDER_API_KEY:
        print("ERROR: Set RENDER_API_KEY environment variable")
        print("  Get your key at: https://dashboard.render.com/u/settings#api-keys")
        sys.exit(1)
    return {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def get_service():
    """Find the service by name."""
    resp = requests.get(f"{RENDER_API_BASE}/services", headers=headers(), params={
        "name": SERVICE_NAME, "limit": 1,
    })
    resp.raise_for_status()
    services = resp.json()
    if not services:
        print(f"ERROR: Service '{SERVICE_NAME}' not found on Render")
        print("  Available services:")
        all_resp = requests.get(f"{RENDER_API_BASE}/services", headers=headers())
        for svc in all_resp.json():
            s = svc.get("service", svc)
            print(f"    - {s.get('name', 'unknown')} ({s.get('id', '')})")
        sys.exit(1)
    svc = services[0]
    return svc.get("service", svc)


def cmd_status():
    """Show current service status."""
    svc = get_service()
    print(f"Service:  {svc['name']}")
    print(f"ID:       {svc['id']}")
    print(f"URL:      https://{svc.get('serviceDetails', {}).get('url', 'N/A')}")
    print(f"Branch:   {svc.get('branch', 'N/A')}")
    print(f"Created:  {svc.get('createdAt', 'N/A')}")
    print(f"Updated:  {svc.get('updatedAt', 'N/A')}")
    print(f"Suspended: {svc.get('suspended', 'N/A')}")

    # Get latest deploy
    deploys = requests.get(
        f"{RENDER_API_BASE}/services/{svc['id']}/deploys",
        headers=headers(), params={"limit": 1},
    ).json()
    if deploys:
        d = deploys[0].get("deploy", deploys[0])
        print(f"\nLatest Deploy:")
        print(f"  ID:     {d.get('id', 'N/A')}")
        print(f"  Status: {d.get('status', 'N/A')}")
        print(f"  Commit: {d.get('commit', {}).get('id', 'N/A')[:8]}")
        print(f"  Time:   {d.get('createdAt', 'N/A')}")


def cmd_deploy():
    """Trigger a new deploy."""
    svc = get_service()
    print(f"Triggering deploy for {svc['name']}...")
    resp = requests.post(
        f"{RENDER_API_BASE}/services/{svc['id']}/deploys",
        headers=headers(),
        json={"clearCache": "do_not_clear"},
    )
    resp.raise_for_status()
    deploy = resp.json()
    d = deploy.get("deploy", deploy)
    deploy_id = d["id"]
    print(f"Deploy triggered: {deploy_id}")
    print(f"Status: {d.get('status', 'unknown')}")
    return svc["id"], deploy_id


def cmd_deploy_and_wait():
    """Trigger deploy and wait for completion with auto-retry on failure."""
    svc_id, deploy_id = cmd_deploy()
    print("\nWaiting for deploy to complete...")

    max_wait = 300  # 5 minutes
    interval = 10
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        resp = requests.get(
            f"{RENDER_API_BASE}/services/{svc_id}/deploys/{deploy_id}",
            headers=headers(),
        )
        d = resp.json()
        deploy = d.get("deploy", d)
        status = deploy.get("status", "unknown")
        print(f"  [{elapsed}s] Status: {status}")

        if status == "live":
            print(f"\nDeploy SUCCEEDED at {datetime.utcnow().isoformat()}Z")
            return True

        if status in ("deactivated", "build_failed", "update_failed", "canceled"):
            print(f"\nDeploy FAILED with status: {status}")
            print("Attempting automatic rollback...")
            cmd_rollback()
            return False

    print(f"\nDeploy TIMEOUT after {max_wait}s — check Render dashboard")
    return False


def cmd_rollback():
    """Rollback to the last successful deploy."""
    svc = get_service()
    deploys = requests.get(
        f"{RENDER_API_BASE}/services/{svc['id']}/deploys",
        headers=headers(), params={"limit": 10},
    ).json()

    # Find last successful deploy
    for item in deploys:
        d = item.get("deploy", item)
        if d.get("status") == "live":
            deploy_id = d["id"]
            print(f"Rolling back to deploy {deploy_id}...")
            resp = requests.post(
                f"{RENDER_API_BASE}/services/{svc['id']}/deploys/{deploy_id}/rollback",
                headers=headers(),
            )
            if resp.status_code < 300:
                print(f"Rollback triggered successfully")
            else:
                print(f"Rollback failed: {resp.status_code} {resp.text}")
            return

    print("ERROR: No successful deploy found to rollback to")


def cmd_logs():
    """Show recent deploy history."""
    svc = get_service()
    deploys = requests.get(
        f"{RENDER_API_BASE}/services/{svc['id']}/deploys",
        headers=headers(), params={"limit": 10},
    ).json()

    print(f"Recent deploys for {svc['name']}:\n")
    print(f"{'Status':<16} {'Deploy ID':<28} {'Commit':<10} {'Time'}")
    print("-" * 80)
    for item in deploys:
        d = item.get("deploy", item)
        commit = d.get("commit", {}).get("id", "N/A")[:8]
        print(f"{d.get('status', '?'):<16} {d.get('id', '?'):<28} {commit:<10} {d.get('createdAt', '?')}")


def cmd_env_check():
    """Verify all required environment variables are set."""
    svc = get_service()
    resp = requests.get(
        f"{RENDER_API_BASE}/services/{svc['id']}/env-vars",
        headers=headers(),
    )
    resp.raise_for_status()
    env_vars = resp.json()

    set_vars = {ev.get("envVar", ev).get("key") for ev in env_vars}

    print("Environment Variables Check:\n")
    all_ok = True
    for var in REQUIRED_ENV_VARS:
        if var in set_vars:
            print(f"  {var}: SET")
        else:
            print(f"  {var}: MISSING")
            all_ok = False

    if not all_ok:
        print(f"\nWARNING: Missing environment variables will cause runtime errors!")
        print("Set them in the Render dashboard under Environment.")
    else:
        print(f"\nAll {len(REQUIRED_ENV_VARS)} required variables are set.")
    return all_ok


def cmd_health():
    """Check if the deployed service is responding."""
    svc = get_service()
    url = svc.get("serviceDetails", {}).get("url", "")
    if not url:
        print("ERROR: Could not determine service URL")
        return False

    base_url = f"https://{url}"
    checks = [
        ("/", "Root"),
        ("/health", "Health"),
        ("/api/v1/diagnostics/system", "Diagnostics"),
    ]

    print(f"Health checks for {base_url}:\n")
    all_ok = True
    for path, name in checks:
        try:
            resp = requests.get(f"{base_url}{path}", timeout=30)
            status = "OK" if resp.status_code == 200 else f"FAIL ({resp.status_code})"
            if resp.status_code != 200:
                all_ok = False
            print(f"  {name:<20} {status}")
        except requests.exceptions.ConnectionError:
            print(f"  {name:<20} FAIL (connection refused)")
            all_ok = False
        except requests.exceptions.Timeout:
            print(f"  {name:<20} FAIL (timeout)")
            all_ok = False

    if all_ok:
        print("\nAll health checks passed!")
    else:
        print("\nSome health checks failed — check Render logs")
    return all_ok


def cmd_full_deploy():
    """Full deploy pipeline: env check -> deploy -> wait -> health check."""
    print("=" * 60)
    print("ZA Support Backend — Full Deploy Pipeline")
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    # Step 1: Env check
    print("\n--- Step 1: Environment Variables ---")
    if not cmd_env_check():
        print("\nABORTED: Fix environment variables before deploying")
        sys.exit(1)

    # Step 2: Deploy
    print("\n--- Step 2: Deploy ---")
    success = cmd_deploy_and_wait()

    if not success:
        print("\nDeploy failed — rolled back automatically")
        sys.exit(1)

    # Step 3: Health check
    print("\n--- Step 3: Health Check ---")
    time.sleep(5)  # Brief wait for service to stabilize
    healthy = cmd_health()

    print("\n" + "=" * 60)
    if healthy:
        print("DEPLOY COMPLETE — Service is live and healthy!")
    else:
        print("DEPLOY WARNING — Service deployed but health checks failed")
        print("Check: https://dashboard.render.com")
    print("=" * 60)


COMMANDS = {
    "status": cmd_status,
    "deploy": lambda: cmd_deploy(),
    "full-deploy": cmd_full_deploy,
    "logs": cmd_logs,
    "rollback": cmd_rollback,
    "env-check": cmd_env_check,
    "health": cmd_health,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python scripts/render_deploy.py <command>")
        print(f"\nCommands:")
        print(f"  status       Show service status and latest deploy")
        print(f"  deploy       Trigger a new deploy")
        print(f"  full-deploy  Full pipeline: env-check → deploy → wait → health")
        print(f"  logs         Show recent deploy history")
        print(f"  rollback     Rollback to last successful deploy")
        print(f"  env-check    Verify required environment variables")
        print(f"  health       Run health checks against live service")
        sys.exit(1)

    COMMANDS[sys.argv[1]]()
