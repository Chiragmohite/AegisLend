"""Upload actual bundled knowledge through existing routes and query as a customer."""
import json
from pathlib import Path
from app.domain_models import KnowledgeDocument
from test_integrated import system, identity

QUESTIONS=['How does human application review work?','How is loan eligibility calculated?',
           'What documents are required to apply for a loan?','What is the scholarship application deadline?']

def test_knowledge_upload_workflow(system, tmp_path):
    client,factory,*_=system
    customer,_=identity(system)
    admin,_=identity(system,admin=True)
    def ask():
        answers=[]
        for question in QUESTIONS:
            response=client.post('/api/v1/assistant',headers=customer,json={'question':question})
            assert response.status_code==200,response.text
            answers.append(response.json())
        return answers
    before=ask()
    assert before[0]['sources']
    assert all(not before[i]['sources'] for i in [1,2,3])
    folder=Path(__file__).resolve().parents[2]/'docs'/'knowledge'
    ids={}
    for path in sorted(folder.glob('*.md')):
        content=path.read_bytes()
        denied=client.post('/api/v1/admin/documents',headers=customer,files={'file':(path.name,content,'text/markdown')})
        assert denied.status_code==403
        uploaded=client.post('/api/v1/admin/documents',headers=admin,files={'file':(path.name,content,'text/markdown')})
        assert uploaded.status_code==201,uploaded.text
        ids[path.name]=uploaded.json()['id']
        assert uploaded.json()['status']=='local_ready'
        assert client.post('/api/v1/admin/documents',headers=admin,files={'file':(path.name,content,'text/markdown')}).status_code==409
    after=ask()
    assert 'authorized human administrator' in after[0]['answer']
    assert 'five checks' in after[1]['answer']
    assert {s['document_id'] for s in after[1]['sources']}=={ids['eligibility-explained.md']}
    assert all(s['title']=='Academic demonstration policy' for s in after[0]['sources'])
    assert 'illustrative checklist' in after[2]['answer']
    assert 'not official' in after[2]['answer']
    assert ids['academic-demo-illustrative-document-checklist.md'] in [s['document_id'] for s in after[2]['sources']]
    assert not after[3]['sources'] and 'could not find enough' in after[3]['answer']
    with factory() as session:
        for result in after[:3]:
            cited=set()
            for line in result['answer'].split('\n\n')[0].splitlines():
                marker,sentence=line.split('] ',1)
                index=int(marker[1:])-1
                source=result['sources'][index]
                doc=session.get(KnowledgeDocument,source['document_id'])
                assert doc and sentence in source['excerpt']
                assert any(c['chunk']==source['chunk'] and c['text']==source['excerpt'] for c in doc.chunks)
                cited.add(index)
            assert cited==set(range(len(result['sources'])))
    print('\nKNOWLEDGE_RESULTS='+json.dumps({'before':before,'after':after,'uploaded':ids}))
