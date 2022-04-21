import math
import os
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Sequence
from typing import TypeVar

from colorama import Fore
from colorama import Style

if TYPE_CHECKING:
    from pytest_gitdiff.diff import DiffSummary
    from pytest_gitdiff.report import TestOutcome

STAR = "✨"
RAIN = "🌧"
INDENT = "\t"

T = TypeVar("T")


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


@dataclass
class FlatTree(Generic[T]):
    value: T
    children: List["FlatTree[T]"]

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        if self.is_leaf:
            return 0

        return max(child.depth for child in self.children) + 1

    def print(self, clr: Any, level: int = 0) -> None:
        if level >= 0:
            prefix = (INDENT * level).expandtabs(4)
            line = prefix + str(self.value)
            print(color(line, clr))

        for child in self.children:
            child.print(clr, level=level + 1)

    def sort_by_depth(self, inplace: bool = False) -> Optional["FlatTree[T]"]:
        tree = self if inplace else deepcopy(self)
        tree.children.sort(key=lambda c: c.depth, reverse=True)
        return tree if not inplace else None

    @classmethod
    def make_leaf_subtree(cls, value: T, leaves: List[T]) -> "FlatTree[T]":
        return cls(value, [cls(leaf_value, []) for leaf_value in leaves])

    @classmethod
    def from_dict(cls, value: T, dictionary: Dict[T, Any]) -> "FlatTree[T]":
        children = []
        for key, container in dictionary.items():
            if isinstance(container, dict):
                children.append(cls.from_dict(key, container))
            elif isinstance(container, list):
                children.append(cls.make_leaf_subtree(key, container))
            else:
                raise TypeError(
                    f"FlatTree got value of invalid type ({type(container)})"
                )

        return cls(value, children)


def set_by_keys(dictionary: Dict[str, Any], keys: List[str], value: Any) -> None:
    for key in keys[:-1]:
        if key not in dictionary:
            dictionary[key] = {}
        dictionary = dictionary[key]

    last_key = keys[-1]
    if last_key in dictionary:
        dictionary[last_key].append(value)
    else:
        dictionary[last_key] = [value]


def build_tests_tree(tests: Sequence["TestOutcome"]) -> FlatTree:
    tree_dict: Dict[str, Any] = {}
    for test in tests:
        *path, test_name = test.get_node_tokens()
        set_by_keys(tree_dict, path, test_name)
    return FlatTree.from_dict("", tree_dict)


def print_tests_as_tree(tests: Sequence["TestOutcome"], clr: Any) -> None:
    tree: FlatTree[str] = build_tests_tree(tests)
    tree.sort_by_depth(inplace=True)
    tree.print(clr, -1)


def print_summary(diff: "DiffSummary") -> None:
    if diff.empty:
        print(color("No changes so far.", Fore.YELLOW))
        return

    print_delimiter("=", inner="diff summary")
    if len(diff.new) > 0:
        print(color(f"++ {len(diff.new)} tests added", Fore.GREEN))
        print_tests_as_tree(diff.new, Fore.GREEN)
    if len(diff.succeeded) > 0:
        print(color(f"+  {len(diff.succeeded)} tests now pass", Fore.GREEN))
        print_tests_as_tree(diff.succeeded, Fore.GREEN)
    if len(diff.deleted) > 0:
        print(color(f"*  {len(diff.deleted)} tests deleted", Fore.LIGHTRED_EX))
        print_tests_as_tree(diff.deleted, Fore.LIGHTRED_EX)
    if len(diff.failed) > 0:
        print(color(f"-- {len(diff.failed)} tests now fail", Fore.RED))
        print_tests_as_tree(diff.failed, Fore.RED)

    if diff.degradated:
        print_delimiter("=", inner=f"{RAIN} degradated {RAIN}", clr=Fore.RED)
    else:
        print_delimiter("=", inner=f"{STAR} succeeded {STAR}", clr=Fore.GREEN)


def print_crashes(diff: "DiffSummary") -> None:
    for test in diff.failed:
        print_delimiter("-", inner=test.nodeid, clr=Fore.RED)
        print(test.error)
