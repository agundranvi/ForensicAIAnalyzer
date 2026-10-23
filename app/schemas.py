from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CaseCreate(Input):
    reference: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(default="", max_length=20000)
    category: str = Field(default="Other cybercrime investigations", max_length=100)


class CaseUpdate(Input):
    notes: str | None = Field(default=None, max_length=50000)
    device: str | None = Field(default=None, max_length=50000)
    description: str | None = Field(default=None, max_length=20000)
    status: Literal["active", "closed"] | None = None


class Query(Input):
    question: str = Field(min_length=1, max_length=2000)


class ReportDraft(Input):
    body: str = Field(default="", max_length=100000)
    artifact_ids: list[int] = Field(default_factory=list, max_length=200)
