import argparse
import math
import os
import subprocess
import sys
import traceback
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

    parser.add_argument("init_rev", type=git_revision)
    parser.add_argument("--cmp", "-c", dest="cmp_rev", type=git_revision, default=None)
    parser.add_argument("--no-summary", action="store_true")
    parser.add_argument("--silent", "-s", action="store_true")
    parser.add_argument("--print-new-fails", "-p", action="store_true")
    parser.add_argument("-a", "--args", nargs=argparse.REMAINDER, default=())

    return parser.parse_args()


def configure_subprocess(silent: bool) -> Dict[str, Any]:
    opts: Dict[str, Any] = {}
    if silent:
        opts.update(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return opts


def color(text: str, clr: Any):
    return clr + text + Style.RESET_ALL


def print_delimiter(fill_char: str, inner: str = "", clr: Optional[Any] = None) -> None:
    size = os.get_terminal_size().columns
    size = size - len(inner) - 2
    half_fill = fill_char * (math.ceil(size / 2))
    line = half_fill + f"{inner}" + half_fill
    if clr is not None:
        line = color(line, clr)

    print(line)


def print_summary(diff: DiffSummary) -> None:
    if diff.empty:
        print(color("No changes so far.", Fore.YELLOW))
        return

    print_delimiter("=", inner="diff summary")
    if len(diff.new) > 0:
        print(color(f"++ {len(diff.new)} tests added", Fore.GREEN))
    if len(diff.succeeded) > 0:
        print(color(f"+  {len(diff.succeeded)} tests now pass", Fore.GREEN))
    if len(diff.deleted) > 0:
        print(color(f"*  {len(diff.deleted)} tests deleted", Fore.LIGHTRED_EX))
    if len(diff.failed) > 0:
        print(color(f"-- {len(diff.failed)} tests now fail", Fore.RED))

    if diff.degradated:
        print_delimiter("=", inner=f"{RAIN} degradated {RAIN}", clr=Fore.RED)
    else:
        print_delimiter("=", inner=f"{STAR} succeeded {STAR}", clr=Fore.GREEN)


def print_crashes(diff: DiffSummary) -> None:
    for test in diff.failed:
        print_delimiter("-", inner=test.nodeid, color=Fore.RED)
        print(test.error)


def main() -> NoReturn:
    arguments = cmdline_arguments()
    try:
        opts = configure_subprocess(arguments.silent)
        diff = diff_revisions(
            pytest_args=arguments.args,
            init_rev=arguments.init_rev,
            cmp_rev=arguments.cmp_rev,
            options=opts,
        )

        if arguments.print_new_fails:
            print_crashes(diff)

        if not arguments.no_summary:
            print_summary(diff)
    except Exception:
        traceback.print_exc()
        print(Fore.RED + "Irrecoverable error caught, terminating" + Style.RESET_ALL)
        sys.exit(2)
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(2)
    else:
        sys.exit(1 if diff.degradated else 0)


if __name__ == "__main__":
    main()
