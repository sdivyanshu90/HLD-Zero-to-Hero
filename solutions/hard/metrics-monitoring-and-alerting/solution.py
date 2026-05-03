from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Tuple


@dataclass(slots=True)
class Sample:
    metric: str
    labels: tuple[tuple[str, str], ...]
    minute_bucket: str
    value: float


class MetricsPlatform:
    def __init__(self, cardinality_limit: int = 5) -> None:
        self.cardinality_limit = cardinality_limit
        self._samples: list[Sample] = []
        self._series_by_metric: DefaultDict[str, set[tuple[tuple[str, str], ...]]] = defaultdict(set)
        self._aggregates: DefaultDict[tuple[str, str], list[float]] = defaultdict(list)

    def ingest(self, metric: str, labels: dict[str, str], minute_bucket: str, value: float) -> None:
        label_tuple = tuple(sorted(labels.items()))
        series = self._series_by_metric[metric]
        if label_tuple not in series and len(series) >= self.cardinality_limit:
            raise ValueError(f"cardinality limit exceeded for metric {metric}")

        series.add(label_tuple)
        sample = Sample(metric=metric, labels=label_tuple, minute_bucket=minute_bucket, value=value)
        self._samples.append(sample)
        self._aggregates[(metric, minute_bucket)].append(value)

    def query_average(self, metric: str, minute_bucket: str) -> float:
        values = self._aggregates[(metric, minute_bucket)]
        return sum(values) / len(values)

    def downsample_average(self, metric: str) -> dict[str, float]:
        return {
            minute_bucket: sum(values) / len(values)
            for (current_metric, minute_bucket), values in self._aggregates.items()
            if current_metric == metric
        }

    def evaluate_threshold_alert(self, metric: str, minute_bucket: str, threshold: float) -> bool:
        return self.query_average(metric, minute_bucket) > threshold


def main() -> None:
    platform = MetricsPlatform(cardinality_limit=3)
    platform.ingest("cpu_usage", {"service": "timeline", "region": "us-east"}, "10:00", 72.0)
    platform.ingest("cpu_usage", {"service": "timeline", "region": "us-east"}, "10:00", 88.0)
    platform.ingest("cpu_usage", {"service": "timeline", "region": "us-west"}, "10:01", 65.0)

    print("averages:", platform.downsample_average("cpu_usage"))
    print("alert fired:", platform.evaluate_threshold_alert("cpu_usage", "10:00", threshold=75.0))


if __name__ == "__main__":
    main()