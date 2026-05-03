from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Operation:
    author_id: str
    kind: str
    position: int
    base_version: int
    text: str = ""
    length: int = 0


class CollaborativeDocument:
    def __init__(self, initial_content: str = "") -> None:
        self.content = initial_content
        self.version = 0
        self._applied_operations: list[Operation] = []

    def apply(self, operation: Operation) -> int:
        rebased = self._rebase(operation)
        if rebased.kind == "insert":
            self.content = self.content[: rebased.position] + rebased.text + self.content[rebased.position :]
        elif rebased.kind == "delete":
            self.content = self.content[: rebased.position] + self.content[rebased.position + rebased.length :]
        else:
            raise ValueError("unknown operation kind")

        self.version += 1
        self._applied_operations.append(
            Operation(
                author_id=rebased.author_id,
                kind=rebased.kind,
                position=rebased.position,
                base_version=self.version,
                text=rebased.text,
                length=rebased.length,
            )
        )
        return self.version

    def _rebase(self, operation: Operation) -> Operation:
        position = operation.position
        for applied in self._applied_operations[operation.base_version :]:
            if applied.kind == "insert" and applied.position <= position:
                position += len(applied.text)
            elif applied.kind == "delete" and applied.position < position:
                position -= min(applied.length, position - applied.position)

        return Operation(
            author_id=operation.author_id,
            kind=operation.kind,
            position=position,
            base_version=self.version,
            text=operation.text,
            length=operation.length,
        )


def main() -> None:
    document = CollaborativeDocument("hello world")
    first = Operation(author_id="alice", kind="insert", position=5, base_version=0, text=",")
    second = Operation(author_id="bob", kind="insert", position=5, base_version=0, text=" brave")

    document.apply(first)
    document.apply(second)

    print("version:", document.version)
    print("content:", document.content)


if __name__ == "__main__":
    main()