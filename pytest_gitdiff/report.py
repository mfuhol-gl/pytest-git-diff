from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pydantic


class FrozenBaseModel(pydantic.BaseModel):
    class Config(pydantic.BaseConfig):
        frozen = True


class TestSummary(FrozenBaseModel):
    passed: int
    failed: int
    total: int
    collected: int


class CrashSummary(FrozenBaseModel):
    path: str
    lineno: int
    message: str


class TestPhaseOutcome(FrozenBaseModel):
    duration: float
    outcome: str
    crash: Optional[CrashSummary] = None
    traceback: Optional[List[CrashSummary]] = None
    longrepr: Optional[str] = None

    @property
    def passed(self):
        return self.outcome == "passed"


class TestOutcome(FrozenBaseModel):
    nodeid: str
    lineno: int
    outcome: str
    setup: TestPhaseOutcome
    call: Optional[TestPhaseOutcome] = None
    teardown: Optional[TestPhaseOutcome] = None

    @property
    def passed(self):
        return self.outcome == "passed"

    @property
    def error(self) -> Optional[str]:
        if self.passed:
            return None

        for phase in (self.setup, self.call, self.teardown):
            if phase is not None and not phase.passed:
                return phase.longrepr

        raise RuntimeError(f"Unable to find failure reason for test {self.nodeid}")


class TestReport(FrozenBaseModel):
    created: float
    duration: float
    exitcode: int
    root: str
    environment: Dict[str, Any]
    summary: TestSummary
    tests: List[TestOutcome]
