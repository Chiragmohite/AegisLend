"""Build a source-only archive and reject accidental inclusion of known local secret values."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import argparse

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=root.parent/'AegisLend_AI_Complete.zip')
args=parser.parse_args()
exclude={'.venv','node_modules','__pycache__','.pytest_cache','dist','.git','var','test-results','playwright-report','.vite','htmlcov'}
secret_values=[]
for env in [root/'.env',root/'backend/.env',root/'frontend/.env']:
    if not env.exists():continue
    for line in env.read_text().splitlines():
        name,separator,value=line.partition('=')
        if separator and name.strip() in {'DB_PASSWORD','MYSQL_PASSWORD','MYSQL_ROOT_PASSWORD','JWT_SECRET','LLM_API_KEY'}:
            value=value.strip().strip('"').strip("'")
            if value and not value.startswith('replace-'):secret_values.append(value.encode())
output=args.output.resolve()
output.parent.mkdir(parents=True,exist_ok=True)
count=0
with ZipFile(output,'w',ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.resolve()==output:continue
        if any(p in exclude for p in path.relative_to(root).parts):continue
        if path.name.startswith('.env') and path.name!='.env.example':continue
        if path.suffix in {'.zip','.joblib','.db','.sqlite','.pyc'} or path.name=='.coverage':continue
        data=path.read_bytes()
        if any(value in data for value in secret_values):raise SystemExit('Secret scan failed for '+str(path.relative_to(root)))
        archive.writestr(str(Path(root.name)/path.relative_to(root)),data);count+=1
with ZipFile(output) as archive:
    if archive.testzip() is not None:raise SystemExit('Archive integrity check failed')
print(f'Created {output} ({count} files). Secret exclusion and ZIP integrity checks passed.')
