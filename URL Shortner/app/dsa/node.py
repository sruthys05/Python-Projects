from typing import Generic, TypeVar

Key = TypeVar("Key")
Value = TypeVar("Value")


class Node(Generic[Key, Value]):
    def __init__(self, key: Key, value: Value) -> None:
        self.key = key
        self.value = value
        self.previous: Node[Key, Value] | None = None
        self.next: Node[Key, Value] | None = None
