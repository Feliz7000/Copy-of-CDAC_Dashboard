import argparse
import os
import sys

import pandas as pd
import requests

BASE_URL = "http://localhost:8000"
TOKEN_URL = os.getenv("TOKEN_URL", f"{BASE_URL}/api/token/")
DEFAULT_BATCH_NAME = os.getenv("BATCH_NAME", "Aug/24")
DEFAULT_OUT_PATH = os.getenv("OUT_PATH", "data/raw/placement_Aug24.parquet")

# Prefer env vars so credentials are not hardcoded in source.
USERNAME = os.getenv("API_USERNAME", "admin")
PASSWORD = os.getenv("API_PASSWORD", "admin")
ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN", "")

session = requests.Session()
headers = {}


def build_placement_url(batch_name: str) -> str:
    return f"{BASE_URL}/api/assessments/reports/placement/?batch_name={batch_name}&format=json"


def write_output(df: pd.DataFrame, out_path: str) -> None:
    if out_path.lower().endswith(".csv"):
        df.to_csv(out_path, index=False)
    else:
        df.to_parquet(out_path, index=False)

if ACCESS_TOKEN:
    print("1. Using API_ACCESS_TOKEN from environment...")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
else:
    print("1. Logging in to get token...")
    if not PASSWORD:
        print(
            "API_PASSWORD is not set. Set API_PASSWORD (or API_ACCESS_TOKEN) and retry.",
        )
        sys.exit(1)

    login_resp = session.post(
        TOKEN_URL,
        json={"username": USERNAME, "password": PASSWORD},
    )

    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.status_code} -> {login_resp.text[:300]}")
        print(
            "Tip: verify credentials or run createsuperuser, then export API_USERNAME/API_PASSWORD.",
        )
        sys.exit(1)

    # JWT endpoint returns access/refresh at top-level.
    token_data = login_resp.json()
    token = token_data.get("access") or token_data.get("token")
    if not token and "tokens" in token_data:
        token = token_data["tokens"].get("access")

    if not token:
        print("Login succeeded but no access token in response:", token_data)
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

parser = argparse.ArgumentParser()
parser.add_argument("--batch-name", default=DEFAULT_BATCH_NAME, help="Placement batch to extract, e.g. Feb/25")
parser.add_argument("--out", default=DEFAULT_OUT_PATH, help="Output file path (.csv or .parquet)")
args = parser.parse_args()

placement_url = os.getenv("PLACEMENT_URL", build_placement_url(args.batch_name))

print("2. Fetching placement data...")
r = session.get(placement_url, headers=headers)

if r.status_code == 200:
    data = r.json()
    rows = data.get("results", data)
    df = pd.DataFrame(rows)
    
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    write_output(df, args.out)
    print(f"Success! Wrote {len(df)} rows to {args.out}")
else:
    print(f"Failed to fetch data: {r.status_code} -> {r.text[:300]}")