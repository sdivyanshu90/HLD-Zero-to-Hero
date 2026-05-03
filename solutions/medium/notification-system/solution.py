from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import DefaultDict, Deque, Dict, List, Set


@dataclass(slots=True)
class NotificationRequest:
    user_id: str
    template_id: str
    channels: list[str]
    payload: dict[str, str]
    idempotency_key: str


@dataclass(slots=True)
class NotificationJob:
    user_id: str
    channel: str
    rendered_message: str
    idempotency_key: str


@dataclass(slots=True)
class UserPreferences:
    allowed_channels: Set[str] = field(default_factory=set)


class NotificationService:
    def __init__(self) -> None:
        self._queues: DefaultDict[str, Deque[NotificationJob]] = defaultdict(deque)
        self._preferences: Dict[str, UserPreferences] = {}
        self._seen_requests: Set[str] = set()
        self._delivery_log: list[str] = []

    def set_preferences(self, user_id: str, allowed_channels: set[str]) -> None:
        self._preferences[user_id] = UserPreferences(allowed_channels=set(allowed_channels))

    def enqueue(self, request: NotificationRequest) -> None:
        if request.idempotency_key in self._seen_requests:
            return
        self._seen_requests.add(request.idempotency_key)

        allowed_channels = self._preferences.get(request.user_id, UserPreferences(set(request.channels))).allowed_channels
        for channel in request.channels:
            if channel not in allowed_channels:
                continue

            message = self._render_message(request.template_id, request.payload)
            self._queues[channel].append(
                NotificationJob(
                    user_id=request.user_id,
                    channel=channel,
                    rendered_message=message,
                    idempotency_key=request.idempotency_key,
                )
            )

    def process_next(self, channel: str) -> str | None:
        if not self._queues[channel]:
            return None
        job = self._queues[channel].popleft()
        result = f"delivered channel={job.channel} user={job.user_id} msg={job.rendered_message}"
        self._delivery_log.append(result)
        return result

    def _render_message(self, template_id: str, payload: dict[str, str]) -> str:
        pairs = ", ".join(f"{key}={value}" for key, value in sorted(payload.items()))
        return f"template={template_id} [{pairs}]"

    def delivery_log(self) -> list[str]:
        return list(self._delivery_log)


def main() -> None:
    service = NotificationService()
    service.set_preferences("u1", {"email", "push"})

    service.enqueue(
        NotificationRequest(
            user_id="u1",
            template_id="order-confirmed",
            channels=["push", "email", "sms"],
            payload={"order_id": "o123", "restaurant": "sushi-lab"},
            idempotency_key="evt-1",
        )
    )

    print(service.process_next("push"))
    print(service.process_next("email"))
    print(service.process_next("sms"))


if __name__ == "__main__":
    main()