"""
Standalone Odoo JSON-RPC Connection Test
Verifies authentication and data retrieval from running Odoo instance.
"""

import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Odoo configuration
ODOO_URL = "http://localhost:8069"
ODOO_DB = os.getenv("ODOO_DB", "ai_employee_db")
ODOO_USERNAME = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASS", "admin")

JSONRPC_URL = f"{ODOO_URL}/jsonrpc"
HEADERS = {"Content-Type": "application/json"}


def authenticate(db: str, username: str, password: str) -> int:
    """
    Authenticate with Odoo via JSON-RPC common/login.
    Returns uid if successful, raises exception on failure.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "common",
            "method": "login",
            "args": [db, username, password]
        },
        "id": 1
    }

    response = requests.post(JSONRPC_URL, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()

    result = response.json()

    if "error" in result:
        error = result["error"]
        raise Exception(f"Authentication failed: {error.get('data', {}).get('message', error.get('message', 'Unknown error'))}")

    uid = result.get("result")

    if not uid or uid <= 0:
        raise Exception("Authentication failed: Invalid credentials or database")

    return uid


def search_partners(uid: int, db: str, password: str, limit: int = 3) -> list:
    """
    Search and read partners from Odoo via JSON-RPC object/execute_kw.
    Returns list of partner records.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [
                db,
                uid,
                password,
                "res.partner",
                "search_read",
                [[]],  # Empty domain = all partners
                {
                    "fields": ["name"],
                    "limit": limit
                }
            ]
        },
        "id": 2
    }

    response = requests.post(JSONRPC_URL, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()

    result = response.json()

    if "error" in result:
        error = result["error"]
        raise Exception(f"search_read failed: {error.get('data', {}).get('message', error.get('message', 'Unknown error'))}")

    return result.get("result", [])


def main():
    """Main test function."""
    print("=" * 60)
    print("Odoo JSON-RPC Connection Test")
    print("=" * 60)
    print(f"URL: {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"Username: {ODOO_USERNAME}")
    print("=" * 60)

    try:
        # Step 1: Authenticate
        print("\n[1/2] Authenticating...")
        uid = authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
        print(f"✓ Authentication successful")
        print(f"  UID: {uid}")

        # Step 2: Search partners
        print("\n[2/2] Reading partners (res.partner)...")
        partners = search_partners(uid, ODOO_DB, ODOO_PASSWORD, limit=3)
        print(f"✓ Retrieved {len(partners)} partner(s):")

        for i, partner in enumerate(partners, 1):
            print(f"  {i}. {partner.get('name', 'N/A')}")

        print("\n" + "=" * 60)
        print("TEST PASSED - Odoo JSON-RPC connection verified")
        print("=" * 60)

    except requests.exceptions.ConnectionError as e:
        print(f"\n✗ Connection failed: {e}")
        print("  Ensure Odoo is running at http://localhost:8069")
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        exit(1)

    except requests.exceptions.Timeout as e:
        print(f"\n✗ Request timeout: {e}")
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        exit(1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        exit(1)


if __name__ == "__main__":
    main()
