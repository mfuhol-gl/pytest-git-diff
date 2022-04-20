from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pydantic


class TestSummary(pydantic.BaseModel):
    passed: int
    failed: int
    total: int
    collected: int


class CrashSummary(pydantic.BaseModel):
    path: str
    lineno: int
    message: str


class TestPhaseOutcome(pydantic.BaseModel):
    duration: float
    outcome: str
    crash: Optional[CrashSummary] = None
    traceback: Optional[List[CrashSummary]] = None
    longrepr: Optional[str] = None

    @property
    def passed(self):
        return self.outcome == "passed"


class TestOutcome(pydantic.BaseModel):
    nodeid: str
    lineno: int
    outcome: str
    setup: TestPhaseOutcome
    call: TestPhaseOutcome
    teardown: TestPhaseOutcome

    @property
    def passed(self):
        return self.outcome == "passed"


class TestReport(pydantic.BaseModel):
    created: float
    duration: float
    exitcode: int
    root: str
    environment: Dict[str, Any]
    summary: TestSummary
    tests: List[TestOutcome]
