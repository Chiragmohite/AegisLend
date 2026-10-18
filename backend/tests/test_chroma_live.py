"""Optional real Chroma HTTP process, isolated temporary storage, no model downloads."""
import os
from pathlib import Path
import shutil
import sys
import socket
import subprocess
import time
import uuid
import pytest
from app.config import Settings
from app.domain_models import KnowledgeDocument
from app import rag


@pytest.mark.skipif(os.getenv('RUN_CHROMA_TESTS')!='1',reason='Opt-in local Chroma HTTP integration')
def test_chroma_http_index_query_delete(tmp_path):
    executable=shutil.which('chroma') or str(Path(sys.executable).parent/('chroma.exe' if os.name=='nt' else 'chroma'))
    assert Path(executable).exists(),'Install requirements-ai.txt in this environment'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    settings=Settings(_env_file=None,db_password='unused-synthetic-test-setting',chroma_enabled=True,chroma_url=f'http://127.0.0.1:{port}')
    with (tmp_path/'chroma.log').open('w') as log:
        process=subprocess.Popen([executable,'run','--path',str(tmp_path/'vectors'),'--host','127.0.0.1','--port',str(port)],stdout=log,stderr=log,env={**os.environ,'ANONYMIZED_TELEMETRY':'False'})
        try:
            deadline=time.monotonic()+20
            while True:
                try:collection=rag.chroma_collection(settings);break
                except Exception:
                    if time.monotonic()>deadline or process.poll() is not None:raise AssertionError('Chroma HTTP server failed to start')
                    time.sleep(.2)
            content,chunks,digest=rag.extract('reference.md',b'Synthetic appointment consultations are scheduled on weekdays. Human reviewers decide loan applications.')
            doc=KnowledgeDocument(id=str(uuid.uuid4()),title='Synthetic reference',content=content,chunks=chunks,content_hash=digest)
            rag.index_document(doc,settings)
            assert doc.status=='vector_ready',doc.error
            result=rag.answer('weekday appointment consultations',[doc],settings)
            assert result['sources'] and result['retrieval']=='chroma_with_local_validation'
            collection.delete(where={'document_id':doc.id})
            assert collection.count()==0
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
