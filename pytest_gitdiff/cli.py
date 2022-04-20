import argparse
import os
import subprocess
import sys
from typing import Any
from typing import Dict
from typing import NoReturn
from typing import Optional

from colorama import Fore
from colorama import Style

from pytest_gitdiff.diff import DiffSummary
from pytest_gitdiff.diff import diff_revisions
from pytest_gitdiff.diff import ensure_rev_exists
from pytest_gitdiff.errors import InvalidGitRevision

STAR = "✨"
RAIN = "🌧"


def git_revision(rev: str) -> str:
    try:
        ensure_rev_exists(rev)
        return rev
    except InvalidGitRevision as err:
        raise ValueError("Invalid git revision") from err


def cmdline_arguments():
    parser = argparse.ArgumentParser(
        "pytest-git-diff",
        description="A tool for comparing pytest runs on different git revisions",
    )

    parser.add_argument("init-rev", type=git_revision)
    parser.add_argument("--cmp-rev", dest="cmp_rev", type=git_revision, default=None)
    parser.add_argument("--no-summary", action="store_true")
    parser.add_argument("--silent", "-s", action="store_true")
    parser.add_argument("--print-crashes", action="store_true")
    parser.add_argument("-a", "--args", nargs=argparse.REMAINDER, default=())

    return parser.parse_args()


def configure_subprocess(silent: bool) -> Dict[str, Any]:
    opts: Dict[str, Any] = {}
    if silent:
        opts.update(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return opts


def print_delimiter(
    fill_char: str, inner: str = "", color: Optional[Any] = None
) -> None:
    size = os.get_terminal_size().columns
    size = size - len(inner)
    half_fill = fill_char * (size // 2 - 1)
    if color is not None:
        half_fill = color + half_fill + Style.RESET_ALL

    print(half_fill + f" {inner} " + half_fill)


def print_summary(diff: DiffSummary) -> None:
    print_delimiter(inner="diff summary")
    if len(diff.new) > 0:
        print(Fore.GREEN + f"++ {len(diff.new)} tests added" + Style.RESET_ALL)
    if len(diff.succeeded) > 0:
        print(Fore.GREEN + f"+  {len(diff.succeeded)} tests now pass" + Style.RESET_ALL)
    if len(diff.deleted) > 0:
        print(
            Fore.LIGHTRED_EX + f"*  {len(diff.deleted)} tests delete" + Style.RESET_ALL
        )
    if len(diff.failed) > 0:
        print(Fore.RED + f"-- {len(diff.failed)} tests now fail" + Style.RESET_ALL)

    if diff.degradated:
        print_delimiter("=", inner=f"{RAIN} degradated {RAIN}", color=Fore.RED)
    else:
        print_delimiter("=", inner=f"{STAR} succeeded {STAR}", color=Fore.GREEN)


def print_crashes(diff: DiffSummary) -> None:
    for test in diff.failed:
        print_delimiter("-", inner=test.nodeid, color=Fore.RED)
        print(test.error)


def main() -> NoReturn:
    arguments = cmdline_arguments()

    opts = configure_subprocess(arguments.silent)
    diff = diff_revisions(
        pytest_args=arguments.args,
        init_rev=arguments.init_rev,
        cmp_rev=arguments.cmp_rev,
        options=opts,
    )

    if arguments.print_crashes:
        print_crashes(diff)

    if not arguments.no_summary:
        print_summary(diff)

    sys.exit(1 if diff.degradated else 0)


if __name__ == "__main__":
    main()
