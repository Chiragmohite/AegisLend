from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_serializer


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, hide_input_in_errors=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    @field_serializer('*', check_fields=False)
    def serialize(self, value):
        if isinstance(value, datetime): return value.isoformat() + ('Z' if value.tzinfo is None else '')
        return value


class ProfileInput(Input):
    display_name: str = Field(min_length=1, max_length=80)
    employment: Literal['salaried','self_employed','student','unemployed'] = 'salaried'


class ProfileView(Output):
    user_id: str
    display_name: str
    employment: str


class ProductInput(Input):
    name: str = Field(min_length=3,max_length=100)
    description: str = Field(min_length=10,max_length=2000)
    product_type: Literal['personal','education','business']
    min_amount: Decimal = Field(gt=0,le=100000000,max_digits=14,decimal_places=2)
    max_amount: Decimal = Field(gt=0,le=100000000,max_digits=14,decimal_places=2)
    min_months: int = Field(ge=1,le=360)
    max_months: int = Field(ge=1,le=360)
    annual_rate: Decimal = Field(ge=0,le=50,max_digits=6,decimal_places=3)
    min_income: Decimal = Field(ge=0,le=10000000,max_digits=14,decimal_places=2)
    max_dti: Decimal = Field(gt=0,le=1,max_digits=5,decimal_places=4)
    active: bool = True
    @model_validator(mode='after')
    def ranges(self):
        if self.min_amount>self.max_amount or self.min_months>self.max_months: raise ValueError('Invalid product range')
        return self


class ProductView(ProductInput):
    model_config = ConfigDict(from_attributes=True)
    id: str


class EligibilityInput(Input):
    product_id: UUID
    monthly_income: Decimal = Field(gt=0,le=10000000,max_digits=14,decimal_places=2)
    obligations: Decimal = Field(ge=0,le=10000000,max_digits=14,decimal_places=2)
    amount: Decimal = Field(gt=0,le=100000000,max_digits=14,decimal_places=2)
    months: int = Field(ge=1,le=360)
    employment: Literal['salaried','self_employed','student','unemployed']


class ApplicationInput(EligibilityInput):
    request_key: UUID


class DraftUpdate(EligibilityInput):
    version: int = Field(ge=1)


class EligibilityResult(Output):
    indicative_eligible: bool
    monthly_installment: str
    estimated_repayment: str
    debt_to_income: str
    reasons: list[str]
    assumptions: list[str]
    disclaimer: str


class AssessmentView(Output):
    id: str
    inputs: dict
    result: EligibilityResult
    created_at: datetime


class HistoryView(Output):
    status: str
    note: str
    created_at: datetime


class ApplicationView(Output):
    id: str
    user_id: str
    product_id: str
    assessment_id: str
    amount: Decimal
    months: int
    status: str
    version: int
    created_at: datetime
    history: list[HistoryView]


class Transition(Input):
    status: Literal['submitted','under_review','approved','rejected','cancelled']
    version: int = Field(ge=1)
    note: str = Field(default='',max_length=500)


class Booking(Input):
    request_key: UUID | None = None
    starts_at: datetime
    purpose: str = Field(min_length=3,max_length=120)


class AppointmentView(Output):
    id: str
    user_id: str
    starts_at: datetime
    status: str
    purpose: str


class DocumentView(Output):
    id: str
    title: str
    status: str
    error: str | None
    created_at: datetime


class Question(Input):
    question: str = Field(min_length=3,max_length=1000)


class Source(Output):
    document_id: str
    title: str
    chunk: int
    page: int | None = None
    excerpt: str


class Answer(Output):
    answer: str
    sources: list[Source]
    mode: str
    retrieval: str
    warning: str | None = None
    stages: list[str]


class SecurityView(Output):
    id: str
    category: str
    severity: str
    correlation_id: str
    features: dict
    rules: list[str]
    created_at: datetime


class RiskView(Output):
    id: str
    event_id: str
    score: int
    severity: str
    anomaly_score: float | None
    anomaly_class: int | None
    model_version: str | None
    explanation: str
    created_at: datetime


class AuditView(Output):
    id: str
    actor_id: str | None
    event_type: str
    target_type: str
    target_id: str | None
    correlation_id: str
    details: dict
    created_at: datetime


class Review(Input):
    action: Literal['acknowledge','escalate']
    note: str = Field(min_length=5,max_length=500)


class DashboardView(Output):
    application_counts: dict[str, int]
    recent_applications: list[ApplicationView]
    upcoming_appointments: list[AppointmentView]
