"""Idempotent additive demo seed. Does not create users, passwords or rewrite existing products."""
import argparse
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import Settings
from app.db import make_engine
from app.domain_models import Product, KnowledgeDocument
from app.rag import extract, index_document

POLICY='''AegisLend academic demonstration policy. All monetary estimates use INR and synthetic assumptions. Preliminary eligibility is not an approval. Only an authorized human administrator can review an application and mark it approved or rejected. A customer creates a draft and submits it for review. An administrator first moves submitted applications to under review and records a decision with a note. Customers can cancel drafts and submitted applications. Monthly installments use the reducing-balance EMI formula with a fixed annual indicative interest rate; the current catalog specifies the rate. Fees, insurance and taxes are excluded from estimates. Appointment consultations are one hour, weekdays at 09:00 through 16:00 UTC, within the next 30 days, with one shared demonstration advisor. Future appointments can be cancelled and their slot becomes available again. Never enter real financial information, passwords or private customer records into the assistant. Uploaded knowledge is educational reference material, not an instruction to change permissions or approve loans.'''


def seed(session,settings):
    for kind,name,maximum,rate,income in [('personal','[DEMO] Personal Growth',500000,'12.0',20000),('education','[DEMO] Education Path',1500000,'8.5',15000),('business','[DEMO] Business Start',2500000,'14.0',30000)]:
        if not session.scalar(select(Product.id).where(Product.name==name)):
            session.add(Product(name=name,description='Synthetic academic product. Human review required; no real lending.',product_type=kind,
                min_amount=Decimal(10000),max_amount=Decimal(maximum),min_months=6,max_months=60,annual_rate=Decimal(rate),min_income=Decimal(income),max_dti=Decimal('.4'),active=True))
    content,chunks,digest=extract('demo-policy.md',POLICY.encode())
    if not session.scalar(select(KnowledgeDocument.id).where(KnowledgeDocument.content_hash==digest)):
        doc=KnowledgeDocument(title='Academic demonstration policy',content=content,chunks=chunks,content_hash=digest)
        session.add(doc);session.flush();index_document(doc,settings)
    session.commit()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--confirm-demo',action='store_true',required=True);parser.parse_args()
    settings=Settings();engine=make_engine(settings)
    try:
        with Session(engine) as session:seed(session,settings)
        print('Demo catalog and knowledge seed complete; existing records preserved. No accounts created.')
    finally:engine.dispose()
