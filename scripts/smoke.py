"""Exercise real Vite → FastAPI HTTP traffic. Requires installed dependencies/env files."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--expect-ready', action='store_true', help='Require migrated MySQL readiness')
args = parser.parse_args()


def get(path):
    try:
        with urlopen('http://127.0.0.1:5173' + path, timeout=8) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


processes = []
with tempfile.TemporaryFile() as logs:
    try:
        processes.append(subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory',
             '--host', '127.0.0.1', '--port', '8000'], cwd=root/'backend', stdout=logs, stderr=logs))
        processes.append(subprocess.Popen(
            [shutil.which('node') or 'node', 'node_modules/vite/bin/vite.js'],
            cwd=root/'frontend', stdout=logs, stderr=logs))
        deadline = time.monotonic() + 30
        while True:
            if any(p.poll() is not None for p in processes):
                raise RuntimeError('A server exited during startup; check ports 8000 and 5173.')
            try:
                status, payload = get('/api/v1/health/live')
                if status == 200:
                    break
            except (URLError, TimeoutError, ConnectionError):
                pass
            if time.monotonic() > deadline:
                raise RuntimeError('Servers did not become available within 30 seconds')
            time.sleep(0.25)
        assert json.loads(payload) == {'status': 'ok', 'service': 'aegislend-api'}
        print('PASS: real Vite proxy → FastAPI liveness HTTP 200')
        status, payload = get('/')
        assert status == 200 and b'/src/main.tsx' in payload
        print('PASS: Vite serves React application entry point')
        status, payload = get('/api/v1/health/ready')
        data = json.loads(payload)
        if args.expect_ready:
            assert status == 200 and data['database'] == 'ready'
            print('PASS: real MySQL readiness HTTP 200')
        else:
            assert (status, data['database']) in [(200, 'ready'), (503, 'unavailable')]
            print(f'PASS: readiness contract HTTP {status}; database={data["database"]}')
        assert all(p.poll() is None for p in processes)
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
