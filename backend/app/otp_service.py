"""RFC 6238 authenticator OTPs. Secret encryption uses the configured JWT key.
Key rotation requires re-enrollment; never log enrollment secrets or OTP inputs.
"""
import base64, hashlib, hmac, secrets, struct, time
from cryptography.fernet import Fernet
from sqlalchemy import update
from app.enhancement_models import Authenticator

def cipher(settings):
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(('aegislend-totp:'+settings.jwt_secret.get_secret_value()).encode()).digest()))
def generate_secret():return base64.b32encode(secrets.token_bytes(20)).decode()
def code(secret,step):
    digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',step),hashlib.sha1).digest();offset=digest[-1]&15
    return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def verify(db,row,value,settings):
    if not value or len(value)!=6 or not value.isdigit():return False
    try:secret=cipher(settings).decrypt(row.encrypted_secret.encode()).decode()
    except Exception:return False
    current=int(time.time()//30)
    for step in (current-1,current,current+1):
        if step>row.last_step and hmac.compare_digest(code(secret,step),value):
            result=db.execute(update(Authenticator).where(Authenticator.user_id==row.user_id,Authenticator.last_step<step).values(last_step=step))
            return result.rowcount==1
    return False
