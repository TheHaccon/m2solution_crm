from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class ExpenseCategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class ExpenseCategoryOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseCreate(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0)
    spent_on: date
    vendor: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    repeat_monthly: bool = False


class ExpenseUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    spent_on: date | None = None
    vendor: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class ExpenseOut(BaseModel):
    id: int
    category_id: int
    category_name: str
    amount: Decimal
    spent_on: date
    vendor: str | None
    notes: str | None
    receipt_file_id: int | None
    receipt_name: str | None = None
    recurrence_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExpenseRecurrenceUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    vendor: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    active: bool | None = None


class ExpenseRecurrenceOut(BaseModel):
    id: int
    category_id: int
    category_name: str
    amount: Decimal
    vendor: str | None
    notes: str | None
    interval: str
    day_of_month: int
    start_on: date
    next_on: date
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
