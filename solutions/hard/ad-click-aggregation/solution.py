from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, List, Tuple


@dataclass(slots=True)
class Event:
    event_id: str
    campaign_id: str
    minute_bucket: str
    event_type: str


class AdClickAggregator:
    def __init__(self) -> None:
        self._seen_event_ids: set[str] = set()
        self._raw_events: list[Event] = []
        self._window_counts: DefaultDict[tuple[str, str], Dict[str, int]] = defaultdict(lambda: {"impression": 0, "click": 0})

    def ingest(self, event: Event) -> None:
        if event.event_id in self._seen_event_ids:
            return
        self._seen_event_ids.add(event.event_id)
        self._raw_events.append(event)
        self._window_counts[(event.campaign_id, event.minute_bucket)][event.event_type] += 1

    def report(self, campaign_id: str) -> dict[str, dict[str, int]]:
        return {
            bucket: counts
            for (current_campaign_id, bucket), counts in self._window_counts.items()
            if current_campaign_id == campaign_id
        }

    def replay(self, events: Iterable[Event]) -> None:
        self._seen_event_ids.clear()
        self._raw_events.clear()
        self._window_counts.clear()
        for event in events:
            self.ingest(event)


def main() -> None:
    aggregator = AdClickAggregator()
    events = [
        Event("e1", "campaign-a", "2026-05-03T10:00", "impression"),
        Event("e2", "campaign-a", "2026-05-03T10:00", "click"),
        Event("e2", "campaign-a", "2026-05-03T10:00", "click"),
        Event("e3", "campaign-a", "2026-05-03T10:01", "impression"),
    ]
    for event in events:
        aggregator.ingest(event)

    print(aggregator.report("campaign-a"))


if __name__ == "__main__":
    main()