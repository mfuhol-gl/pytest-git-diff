from typing import Any
from typing import FrozenSet
from typing import List
from typing import Optional

import pydantic


class FrozenBaseModel(pydantic.BaseModel):
    class Config(pydantic.BaseConfig):
        frozen = True


class TestSummary(FrozenBaseModel):
    passed: int = 0
    failed: int = 0
    total: int = 0
    collected: int = 0
    deselected: int = 0


class CrashSummary(FrozenBaseModel):
    path: str
    lineno: int
    message: str


class TestPhaseOutcome(FrozenBaseModel):
    outcome: str
    crash: Optional[CrashSummary] = None
    traceback: Optional[FrozenSet[CrashSummary]] = None
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

    def get_node_tokens(self) -> List[str]:
        path, groups = self.nodeid.split("::", maxsplit=1)
        return [path, *groups.split("::")]

    def __hash__(self) -> int:
        return hash(self.nodeid)

    def __eq__(self, other: Any):
        if not isinstance(other, TestOutcome):
            return NotImplemented

        return self.nodeid == other.nodeid

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(nodeid={self.nodeid}, outcome={self.outcome})"
        )


class TestReport(FrozenBaseModel):
    created: float
    duration: float
    exitcode: int
    root: str
    summary: TestSummary
    tests: FrozenSet[TestOutcome]
