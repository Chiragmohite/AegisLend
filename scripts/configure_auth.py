"""Append a new random signing key only when JWT_SECRET is absent. Never print it."""
from pathlib import Path
import os
import re
import secrets

path = Path(__file__).resolve().parents[1] / 'backend/.env'
if not path.exists():
    raise SystemExit('Initialize backend/.env first; see README.md.')
if os.getenv('JWT_SECRET') or re.search(r'^\s*(?:export\s+)?JWT_SECRET\s*=', path.read_text(), re.MULTILINE):
    raise SystemExit('JWT_SECRET already exists. No configuration changed.')
with path.open('a') as stream:
    stream.write('\nJWT_SECRET=' + secrets.token_urlsafe(48) + '\n')
path.chmod(0o600)
print('Added a random signing key to backend/.env without printing it or replacing existing settings.')
