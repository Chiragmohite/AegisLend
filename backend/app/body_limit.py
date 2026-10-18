"""Bound request bodies before JSON/multipart parsing, including chunked requests."""
from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        limit=2*1024*1024+65536 if scope.get('path')=='/api/v1/admin/documents' else 32768
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            body.extend(message.get('body',b''))
            if len(body)>limit:
                return await JSONResponse({'detail':'Request body exceeds size limit'},status_code=413)(scope,receive,send)
            if not message.get('more_body',False):break
        sent=False
        async def bounded_receive():
            nonlocal sent
            if not sent:
                sent=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,bounded_receive,send)
