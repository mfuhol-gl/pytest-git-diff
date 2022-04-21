import argparse
import subprocess
import sys
import traceback
from typing import Any
from typing import Dict
from typing import NoReturn

from colorama import Fore

from pytest_gitdiff.diff import diff_revisions
from pytest_gitdiff.diff import ensure_rev_exists
from pytest_gitdiff.errors import InvalidGitRevision
from pytest_gitdiff.viz import color
from pytest_gitdiff.viz import print_crashes
from pytest_gitdiff.viz import print_summary


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
        print(color("Irrecoverable error caught, terminating", Fore.RED))
        sys.exit(2)
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(2)
    else:
        sys.exit(1 if diff.degradated else 0)


if __name__ == "__main__":
    main()
