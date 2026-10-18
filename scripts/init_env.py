"""Create local-only credentials without overwriting existing configuration."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
paths = [root / '.env', root / 'backend/.env', root / 'frontend/.env']
if any(p.exists() for p in paths):
    raise SystemExit('An environment file already exists. Preserve it and configure missing files manually using .env.example.')
password = secrets.token_urlsafe(32)
root_password = secrets.token_urlsafe(32)
for path in paths:
    template = path.with_name('.env.example').read_text()
    template = template.replace('replace-with-local-development-password', password)
    template = template.replace('replace-with-different-root-password', root_password)
    path.write_text(template)
    path.chmod(0o600)
print('Created local environment files. Existing files were not overwritten; credentials were not printed.')
