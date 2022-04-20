from typing import Any


class InvalidGitRevision(RuntimeError):
    def __init__(self, *args: Any, revision: str) -> None:
        super().__init__(*args)
        self.revision = revision

    @classmethod
    def from_revision(cls, revision: str):
        return cls(f"Invalid git revision {revision}", revision=revision)
