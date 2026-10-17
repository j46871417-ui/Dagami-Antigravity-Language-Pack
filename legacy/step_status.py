"""
Модель статусов и результатов шагов локализации (Раздел 9).
"""

from __future__ import annotations

from enum import Enum


class StepStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ALREADY_DONE = "ALREADY_DONE"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class StepResult:
    def __init__(
        self,
        step_name: str,
        status: StepStatus,
        message: str = "",
        is_mandatory: bool = True,
    ):
        self.step_name = step_name
        self.status = status
        self.message = message
        self.is_mandatory = is_mandatory

    def is_success(self) -> bool:
        return self.status in (StepStatus.SUCCESS, StepStatus.ALREADY_DONE, StepStatus.SKIPPED)

    def __repr__(self) -> str:
        return f"<StepResult {self.step_name}: {self.status.value} (mandatory={self.is_mandatory}) - {self.message}>"
