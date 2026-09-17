import httpx
import time
from datetime import datetime

BASE_URL = 'https://devintel-api-5q0d.onrender.com'
repo_id = '712fd9db-c01d-4495-98f5-0722b9053e33'

# Login to get token
token = httpx.post(f'{BASE_URL}/api/v1/auth/demo', timeout=30).json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Trigger indexing
now_str = datetime.now().strftime('%H:%M:%S')
print(f'[{now_str}] Triggering indexing on repo {repo_id}...')
idx_resp = httpx.post(f'{BASE_URL}/api/v1/repos/index', json={'repository_id': repo_id}, headers=headers, timeout=30)
print(f'Index trigger status: {idx_resp.status_code}')
print(f'Index trigger body: {idx_resp.json()}')

# Polling loop
start = time.time()
for i in range(25):
    now_str = datetime.now().strftime('%H:%M:%S')
    elapsed = int(time.time() - start)
    try:
        r = httpx.get(f'{BASE_URL}/api/v1/repos/{repo_id}/status', headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            st = data.get('indexing_status')
            pr = data.get('indexing_progress')
            err = data.get('indexing_error')
            print(f'[{now_str} | +{elapsed:>3}s] status={st:<10} progress={pr:>3}% error={err}')
            if str(st).lower() in ('complete', 'failed'):
                print(f'\nTerminal state reached: {st} in {elapsed}s')
                break
        else:
            print(f'[{now_str} | +{elapsed:>3}s] HTTP error {r.status_code}: {r.text}')
    except Exception as e:
        print(f'[{now_str} | +{elapsed:>3}s] Exception: {e}')
    time.sleep(10)
