from typing import Generic, TypeVar

from app.dsa.node import Node

Key = TypeVar("Key")
Value = TypeVar("Value")


class LRUCache(Generic[Key, Value]):
    """O(1) LRU cache backed by a dictionary and a doubly linked list."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be greater than zero")
        self.capacity = capacity
        self._nodes: dict[Key, Node[Key, Value]] = {}
        self._most_recent: Node[Key, Value] = Node(None, None)  # type: ignore[arg-type]
        self._least_recent: Node[Key, Value] = Node(None, None)  # type: ignore[arg-type]
        self._most_recent.next = self._least_recent
        self._least_recent.previous = self._most_recent

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, key: object) -> bool:
        return key in self._nodes

    def get(self, key: Key, default: Value | None = None) -> Value | None:
        node = self._nodes.get(key)
        if node is None:
            return default
        self._move_to_front(node)
        return node.value

    def put(self, key: Key, value: Value) -> None:
        node = self._nodes.get(key)
        if node is not None:
            node.value = value
            self._move_to_front(node)
            return

        node = Node(key, value)
        self._nodes[key] = node
        self._insert_after_head(node)
        if len(self._nodes) > self.capacity:
            least_recent = self._least_recent.previous
            assert least_recent is not None and least_recent is not self._most_recent
            self._remove(least_recent)
            del self._nodes[least_recent.key]

    def pop(self, key: Key) -> Value | None:
        node = self._nodes.pop(key, None)
        if node is None:
            return None
        self._remove(node)
        return node.value

    def clear(self) -> None:
        self._nodes.clear()
        self._most_recent.next = self._least_recent
        self._least_recent.previous = self._most_recent

    def _move_to_front(self, node: Node[Key, Value]) -> None:
        self._remove(node)
        self._insert_after_head(node)

    def _insert_after_head(self, node: Node[Key, Value]) -> None:
        first = self._most_recent.next
        assert first is not None
        node.previous = self._most_recent
        node.next = first
        self._most_recent.next = node
        first.previous = node

    @staticmethod
    def _remove(node: Node[Key, Value]) -> None:
        previous = node.previous
        following = node.next
        assert previous is not None and following is not None
        previous.next = following
        following.previous = previous
        node.previous = None
        node.next = None
