import httpx
import time
from datetime import datetime

BASE_URL = "https://devintel-api-5q0d.onrender.com"

def run_test():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Logging in via demo endpoint...")
    login_resp = httpx.post(f"{BASE_URL}/api/v1/auth/demo", timeout=30.0)
    print(f"Login status: {login_resp.status_code}")
    if login_resp.status_code != 200:
        print(f"Demo login failed: {login_resp.text}")
        return
    token = login_resp.json()["access_token"]
    user = login_resp.json()["user"]
    print(f"Logged in as: {user['email']} (id={user['id']})")

    headers = {"Authorization": f"Bearer {token}"}

    # Check existing repos - cleanup if needed
    repos_resp = httpx.get(f"{BASE_URL}/api/v1/repos", headers=headers, timeout=30.0)
    existing_repos = repos_resp.json().get("repositories", [])
    for r in existing_repos:
        if r["full_name"] == "octocat/Spoon-Knife":
            print(f"Cleaning up existing repo {r['id']}...")
            httpx.delete(f"{BASE_URL}/api/v1/repos/{r['id']}", headers=headers, timeout=30.0)

    # Connect repository (POST /api/v1/repos)
    connect_payload = {
        "repo_name": "Spoon-Knife",
        "full_name": "octocat/Spoon-Knife",
        "description": "This repo is for spoon-knife.",
        "url": "https://github.com/octocat/Spoon-Knife",
        "stars": 10000,
        "language": "HTML",
        "default_branch": "main"
    }
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connecting repository...")
    connect_resp = httpx.post(f"{BASE_URL}/api/v1/repos", json=connect_payload, headers=headers, timeout=30.0)
    print(f"Connect status: {connect_resp.status_code}")
    print(f"Connect body: {connect_resp.json()}")
    if connect_resp.status_code != 200:
        print(f"Connect failed: {connect_resp.text}")
        return
    repo_data = connect_resp.json()
    repo_id = repo_data["id"]

    # Trigger indexing immediately (POST /api/v1/repos/index)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Triggering indexing for repo {repo_id}...")
    index_resp = httpx.post(f"{BASE_URL}/api/v1/repos/index", json={"repository_id": repo_id}, headers=headers, timeout=30.0)
    print(f"Index trigger status: {index_resp.status_code}")
    print(f"Index trigger body: {index_resp.json()}")

    # Poll status every 10 seconds for up to 4 minutes (24 iterations)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting polling loop...")
    start_time = time.time()

    for i in range(25):
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = int(time.time() - start_time)
        try:
            status_resp = httpx.get(f"{BASE_URL}/api/v1/repos/{repo_id}/status", headers=headers, timeout=30.0)
            if status_resp.status_code == 200:
                data = status_resp.json()
                st = data.get("indexing_status")
                pr = data.get("indexing_progress")
                er = data.get("indexing_error")
                print(f"[{now_ts} | +{elapsed:>3}s] indexing_status='{st}' | indexing_progress={pr}% | indexing_error={er}")
                if str(st).lower() in ("complete", "failed"):
                    print(f"\nFinal status reached: {st} (in {elapsed} seconds)")
                    break
            else:
                print(f"[{now_ts} | +{elapsed:>3}s] HTTP error {status_resp.status_code}: {status_resp.text}")
        except Exception as e:
            print(f"[{now_ts} | +{elapsed:>3}s] Request exception: {e}")
        time.sleep(10)

if __name__ == "__main__":
    run_test()
