from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class TrieNode:
    children: dict[str, "TrieNode"] = field(default_factory=dict)
    top_suggestions: list[tuple[str, int]] = field(default_factory=list)


class AutocompleteIndex:
    def __init__(self, top_k: int = 5) -> None:
        self.top_k = top_k
        self._root = TrieNode()

    def add_query(self, query: str, score: int) -> None:
        node = self._root
        for character in query:
            node = node.children.setdefault(character, TrieNode())
            self._update_top_suggestions(node, query, score)

    def suggest(self, prefix: str, limit: int = 5) -> list[str]:
        node = self._root
        for character in prefix:
            if character not in node.children:
                return []
            node = node.children[character]
        return [query for query, _score in node.top_suggestions[:limit]]

    def _update_top_suggestions(self, node: TrieNode, query: str, score: int) -> None:
        deduped = {existing_query: existing_score for existing_query, existing_score in node.top_suggestions}
        deduped[query] = max(score, deduped.get(query, 0))
        node.top_suggestions = sorted(deduped.items(), key=lambda item: (-item[1], item[0]))[: self.top_k]


def main() -> None:
    index = AutocompleteIndex(top_k=3)
    index.add_query("system design", 100)
    index.add_query("system design interview", 80)
    index.add_query("system programming", 50)
    index.add_query("search autocomplete", 90)

    print("Suggestions for 'sys':", index.suggest("sys"))
    print("Suggestions for 'sea':", index.suggest("sea"))


if __name__ == "__main__":
    main()