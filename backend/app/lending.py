from decimal import Decimal, ROUND_HALF_UP
from app.schemas import EligibilityInput
from app.domain_models import Product

DISCLAIMER = 'Academic estimate using synthetic assumptions, not a credit decision or guaranteed approval. Human review is required.'


def emi(amount: Decimal, annual_rate: Decimal, months: int) -> Decimal:
    if months < 1 or months > 360 or amount <= 0 or annual_rate < 0 or annual_rate > 50:
        raise ValueError('Invalid EMI input')
    rate = annual_rate / Decimal(1200)
    value = amount / months if rate == 0 else amount * rate * (1+rate)**months / ((1+rate)**months-1)
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def assess(data: EligibilityInput, product: Product) -> dict:
    payment = emi(data.amount, product.annual_rate, data.months)
    ratio = (payment+data.obligations)/data.monthly_income
    checks = [
        (product.min_amount<=data.amount<=product.max_amount, 'Requested amount within product range'),
        (product.min_months<=data.months<=product.max_months, 'Tenure within product range'),
        (data.monthly_income>=product.min_income, 'Income meets indicative minimum'),
        (ratio<=product.max_dti, 'Estimated debt-to-income ratio within product threshold'),
        (data.employment in ['salaried','self_employed'], 'Demonstrated regular income source'),
    ]
    return {'indicative_eligible': all(ok for ok,_ in checks), 'monthly_installment': str(payment),
        'estimated_repayment': str(payment*data.months), 'debt_to_income': str(ratio.quantize(Decimal('0.0001'))),
        'reasons': [('Meets: ' if ok else 'Does not meet: ')+reason for ok,reason in checks],
        'assumptions': [f'INR; fixed indicative annual rate {product.annual_rate}%', 'Monthly reducing balance; rounded installment; fees, insurance and taxes excluded.',f'Debt-to-income limit {product.max_dti}; self-reported synthetic inputs, no credit-bureau check.'],
        'disclaimer': DISCLAIMER}
