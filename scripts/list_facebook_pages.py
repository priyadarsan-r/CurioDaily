"""
Utility script to fetch and list all Facebook Pages and linked Instagram accounts
associated with a Meta User Access Token.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List
import requests

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def list_pages(access_token: str) -> List[Dict[str, Any]]:
    """Fetch pages and linked Instagram accounts from Meta Graph API."""
    url = f"{GRAPH_API_BASE}/me/accounts"
    params = {
        "access_token": access_token,
        "fields": "id,name,category,access_token,instagram_business_account{id,username}",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        if "error" in data:
            print(f"\n❌ Meta API Error: {data['error'].get('message', 'Unknown error')}")
            return []

        pages = data.get("data", [])
        return pages

    except Exception as exc:
        print(f"\n❌ Network/Request Error: {exc}")
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="List Facebook Pages and connected Instagram Business accounts")
    parser.add_argument("--token", type=str, default=None, help="User Access Token from Meta Graph API Explorer")
    args = parser.parse_args()

    token = args.token or os.getenv("FACEBOOK_ACCESS_TOKEN") or os.getenv("INSTAGRAM_ACCESS_TOKEN")

    if not token:
        print("=" * 60)
        print("⚠️ No Access Token Provided!")
        print("=" * 60)
        print("To query Meta for your Facebook Pages, provide an access token:\n")
        print("Usage:")
        print("  python scripts/list_facebook_pages.py --token <YOUR_USER_ACCESS_TOKEN>")
        print("  OR set INSTAGRAM_ACCESS_TOKEN in your environment / .env file.")
        print("\nHow to get a token:")
        print("  1. Go to https://developers.facebook.com/tools/explorer/")
        print("  2. Select your App and click 'Generate Access Token'")
        print("  3. Ensure 'pages_show_list' and 'instagram_basic' permissions are added.")
        sys.exit(1)

    print("\n🔍 Querying Meta Graph API for your Facebook Pages...")
    pages = list_pages(token)

    if not pages:
        print("\nNo Facebook Pages found for this account (or the token lacks 'pages_show_list' permission).")
        return

    print(f"\n✅ Found {len(pages)} Facebook Page(s):\n")
    for idx, page in enumerate(pages, 1):
        print(f"[{idx}] Page Name: {page.get('name')}")
        print(f"    Page ID:   {page.get('id')}")
        print(f"    Category:  {page.get('category', 'N/A')}")

        ig_account = page.get("instagram_business_account")
        if ig_account:
            print(f"    🔗 Linked Instagram:")
            print(f"       Username:   @{ig_account.get('username')}")
            print(f"       Account ID: {ig_account.get('id')}  <-- (Use this as INSTAGRAM_ACCOUNT_ID!)")
        else:
            print(f"    ⚠️ No Instagram Business/Creator account connected to this Page.")
        print("-" * 50)


if __name__ == "__main__":
    main()
