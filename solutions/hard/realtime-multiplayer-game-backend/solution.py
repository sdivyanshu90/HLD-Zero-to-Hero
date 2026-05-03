from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import DefaultDict, Deque, Dict, List


@dataclass(slots=True)
class PlayerQueueEntry:
    player_id: str
    region: str
    skill: int


@dataclass(slots=True)
class MatchSession:
    match_id: str
    region: str
    players: list[str]
    positions: dict[str, int] = field(default_factory=dict)


class MultiplayerGameBackend:
    def __init__(self) -> None:
        self._queues: DefaultDict[str, Deque[PlayerQueueEntry]] = defaultdict(deque)
        self._matches: Dict[str, MatchSession] = {}
        self._next_match_id = 1

    def enqueue_player(self, player_id: str, region: str, skill: int) -> None:
        self._queues[region].append(PlayerQueueEntry(player_id, region, skill))

    def matchmake(self, region: str, match_size: int = 2) -> str:
        queue = self._queues[region]
        if len(queue) < match_size:
            raise ValueError("not enough players in queue")
        players = [queue.popleft().player_id for _ in range(match_size)]
        match_id = f"m{self._next_match_id}"
        self._next_match_id += 1
        self._matches[match_id] = MatchSession(
            match_id=match_id,
            region=region,
            players=players,
            positions={player_id: 0 for player_id in players},
        )
        return match_id

    def submit_input(self, match_id: str, player_id: str, action: str) -> None:
        match = self._matches[match_id]
        if player_id not in match.players:
            raise ValueError("player not in match")
        if action == "move_right":
            match.positions[player_id] += 1
        elif action == "move_left":
            match.positions[player_id] -= 1
        else:
            raise ValueError("unsupported action")

    def snapshot(self, match_id: str) -> dict[str, int]:
        return dict(self._matches[match_id].positions)


def main() -> None:
    backend = MultiplayerGameBackend()
    backend.enqueue_player("p1", region="eu-west", skill=1200)
    backend.enqueue_player("p2", region="eu-west", skill=1180)
    match_id = backend.matchmake("eu-west")
    backend.submit_input(match_id, "p1", "move_right")
    backend.submit_input(match_id, "p2", "move_left")

    print("match:", match_id)
    print("snapshot:", backend.snapshot(match_id))


if __name__ == "__main__":
    main()