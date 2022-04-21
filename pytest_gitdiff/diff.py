import dataclasses
import datetime
import os
import subprocess
import tempfile
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import TypeVar

from git import GitCommandError
from git import Repo

from pytest_gitdiff.errors import InvalidGitRevision
from pytest_gitdiff.report import TestOutcome
from pytest_gitdiff.report import TestReport

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d")
REPO = Repo(os.getcwd())
GIT = REPO.git


T = TypeVar("T")


@dataclasses.dataclass
class DiffSummary:
    succeeded: Sequence[TestOutcome]
    failed: Sequence[TestOutcome]
    new: Sequence[TestOutcome]
    deleted: Sequence[TestOutcome]

    @classmethod
    def from_reports(cls, init: TestReport, cmp: TestReport):
        initial_success = {test for test in init.tests if test.passed}
        initial_fail = {test for test in init.tests if not test.passed}

        return cls(
            succeeded=[
                test for test in cmp.tests if test.passed and test in initial_fail
            ],
            failed=[
                test
                for test in cmp.tests
                if not test.passed and test in initial_success
            ],
            new=list(set(cmp.tests).difference(init.tests)),
            deleted=list(set(init.tests).difference(cmp.tests)),
        )

    @property
    def degradated(self) -> bool:
        return len(self.failed) > 0

    @property
    def empty(self) -> bool:
        return (
            len(self.succeeded) == 0
            and len(self.failed) == 0
            and len(self.new) == 0
            and len(self.deleted) == 0
        )


def run_pytest(*args: str, **opts: Any) -> TestReport:
    with tempfile.TemporaryDirectory(f"pytest-git-diff-{TIMESTAMP}") as tmp:
        json_file = os.path.join(tmp, "dump.json")
        subprocess.run(
            [
                "pytest",
                *args,
                "--json-report",
                "--json-report-file",
                json_file,
            ],
            **opts,
        )

        if not os.path.isfile(json_file):
            raise RuntimeError("Pytest failed at collection phase")

        return TestReport.parse_file(json_file)


def checkout_rev(rev: str, force: bool = False) -> None:
    GIT.checkout(rev, force=force)


def run_pytest_at(rev: str, *args: str, **opts: Any) -> TestReport:
    old_rev = REPO.active_branch.name
    try:
        checkout_rev(rev)
        print(f"Running pytest at {rev} revision")
        return run_pytest(*args, **opts)
    except Exception as err:
        raise RuntimeError(f"Execution at {rev} revision failed") from err
    finally:
        checkout_rev(old_rev)


def ensure_rev_exists(revision: str) -> None:
    initial = REPO.active_branch.name
    try:
        checkout_rev(revision)
    except GitCommandError as err:
        raise InvalidGitRevision.from_revision(revision) from err
    finally:
        checkout_rev(initial)


def diff_revisions(
    pytest_args: List[str],
    init_rev: str,
    cmp_rev: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> DiffSummary:
    options = options or {}
    cmp_rev = cmp_rev or REPO.active_branch.name

    ensure_rev_exists(init_rev)
    if cmp_rev != REPO.active_branch.name:
        ensure_rev_exists(cmp_rev)

    cmp_report = run_pytest_at(cmp_rev, *pytest_args, **options)
    init_report = run_pytest_at(init_rev, *pytest_args, **options)
    diff = DiffSummary.from_reports(init_report, cmp_report)

    return diff
