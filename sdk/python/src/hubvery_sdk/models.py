"""Pydantic models mirroring spec/schemas/*.schema.json.

Uses extra="forbid" throughout to match each schema's
additionalProperties: false constraint.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"
    MULTIMODAL = "multimodal"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    REQUIRES_INPUT = "requires_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Constraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_input_bytes: Optional[int] = Field(default=None, ge=1)
    timeout_seconds: Optional[int] = Field(default=None, ge=1, le=3600)
    supports_human_in_the_loop: bool = False


class CapabilityManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    modality: Modality
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    constraints: Optional[Constraints] = None
    auth_scopes: Optional[list[str]] = Field(default=None, min_length=1)


class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability_id: str
    input: dict[str, Any]
    callback_url: Optional[str] = None
    idempotency_key: Optional[str] = Field(default=None, max_length=128)


class Error(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
    code: Optional[str] = None


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    capability_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    input: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[Error] = None
