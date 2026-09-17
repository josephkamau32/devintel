import sys
import time
from datetime import datetime
import httpx

BASE_URL = "https://devintel-api-5q0d.onrender.com"

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def wait_for_deploy(target_version: str = "1.0.2", timeout_minutes: int = 15):
    log(f"Waiting for Render deployment of version '{target_version}'...")
    start = time.time()
    while time.time() - start < timeout_minutes * 60:
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=20.0)
            if r.status_code == 200:
                data = r.json()
                ver = data.get("version")
                env = data.get("environment")
                if ver == target_version:
                    log(f"SUCCESS: Render deployment is LIVE! version='{ver}', env='{env}'")
                    return True
                else:
                    log(f"Still running older version '{ver}' (waiting for '{target_version}')...")
            else:
                log(f"Health check status {r.status_code}: {r.text[:100]}")
        except Exception as e:
            log(f"Health check transient error (container restarting?): {e}")
        time.sleep(15)
    log(f"TIMEOUT waiting for version '{target_version}' after {timeout_minutes} minutes.")
    return False

def run_connect_and_index():
    log("=== Starting Live Production Connect & Index Test ===")
    
    # 1. Login
    login_resp = httpx.post(f"{BASE_URL}/api/v1/auth/demo", timeout=30.0)
    if login_resp.status_code != 200:
        log(f"FAILED to login via demo endpoint: {login_resp.text}")
        return
    token = login_resp.json()["access_token"]
    user = login_resp.json()["user"]
    log(f"Logged in as demo user: {user['email']} (id={user['id']})")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Cleanup existing Spoon-Knife repos
    repos_resp = httpx.get(f"{BASE_URL}/api/v1/repos", headers=headers, timeout=30.0)
    existing_repos = repos_resp.json().get("repositories", [])
    for r in existing_repos:
        if r["full_name"] == "octocat/Spoon-Knife":
            log(f"Cleaning up existing repo {r['id']}...")
            del_resp = httpx.delete(f"{BASE_URL}/api/v1/repos/{r['id']}", headers=headers, timeout=30.0)
            log(f"Delete status: {del_resp.status_code}")

    # 3. Connect repository (POST /api/v1/repos)
    connect_payload = {
        "repo_name": "Spoon-Knife",
        "full_name": "octocat/Spoon-Knife",
        "description": "This repo is for spoon-knife.",
        "url": "https://github.com/octocat/Spoon-Knife",
        "stars": 10000,
        "language": "HTML",
        "default_branch": "main"
    }
    log("Connecting repository 'octocat/Spoon-Knife' via POST /api/v1/repos...")
    connect_resp = httpx.post(f"{BASE_URL}/api/v1/repos", json=connect_payload, headers=headers, timeout=30.0)
    log(f"Connect status: {connect_resp.status_code}")
    if connect_resp.status_code != 200:
        log(f"Connect FAILED: {connect_resp.text}")
        return
    repo_data = connect_resp.json()
    repo_id = repo_data["id"]
    log(f"Repository created successfully! ID={repo_id}, indexing_mode='{repo_data.get('indexing_mode')}'")

    # 4. Trigger indexing (POST /api/v1/repos/index)
    log(f"Triggering indexing for repo {repo_id} via POST /api/v1/repos/index...")
    index_resp = httpx.post(f"{BASE_URL}/api/v1/repos/index", json={"repository_id": repo_id}, headers=headers, timeout=30.0)
    log(f"Index trigger status: {index_resp.status_code}")
    log(f"Index trigger body: {index_resp.json()}")
    if index_resp.status_code != 200:
        log(f"Index trigger FAILED: {index_resp.text}")
        return

    # 5. Poll status every 10s
    log("Starting status polling loop...")
    start_time = time.time()
    final_status = None
    final_error = None

    for i in range(35): # up to ~6 minutes
        elapsed = int(time.time() - start_time)
        try:
            status_resp = httpx.get(f"{BASE_URL}/api/v1/repos/{repo_id}/status", headers=headers, timeout=30.0)
            if status_resp.status_code == 200:
                data = status_resp.json()
                st = data.get("indexing_status")
                pr = data.get("indexing_progress")
                er = data.get("indexing_error")
                log(f"[+{elapsed:>3}s] indexing_status='{st:<10}' | indexing_progress={pr:>3}% | indexing_error={er}")
                if str(st).lower() in ("complete", "failed"):
                    final_status = st
                    final_error = er
                    log(f"\nTerminal state reached: {st} (in {elapsed} seconds)")
                    break
            else:
                log(f"[+{elapsed:>3}s] Status HTTP error {status_resp.status_code}: {status_resp.text}")
        except Exception as e:
            log(f"[+{elapsed:>3}s] Request error: {e}")
        time.sleep(10)

    # 6. If complete, verify embeddings exist via search
    if str(final_status).lower() == "complete":
        log("\n--- Verifying Stored Embeddings via Search Endpoint ---")
        try:
            search_resp = httpx.get(
                f"{BASE_URL}/api/v1/repos/{repo_id}/search?q=fork&top_k=5",
                headers=headers,
                timeout=30.0,
            )
            log(f"Search status: {search_resp.status_code}")
            if search_resp.status_code == 200:
                results = search_resp.json().get("results", [])
                log(f"Found {len(results)} vector search results in database for query 'fork':")
                for idx, r in enumerate(results[:3]):
                    log(f"  Result {idx+1}: file={r.get('file_path')} similarity={r.get('similarity'):.4f} chunk_index={r.get('chunk_index')}")
                    log(f"    Snippet: {r.get('chunk_text', '')[:120].strip()}...")
            else:
                log(f"Search endpoint response: {search_resp.text}")
        except Exception as search_err:
            log(f"Search verification failed: {search_err}")

if __name__ == "__main__":
    if wait_for_deploy(target_version="1.0.2"):
        run_connect_and_index()
    else:
        sys.exit(1)
