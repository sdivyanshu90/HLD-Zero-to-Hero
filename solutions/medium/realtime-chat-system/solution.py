from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import DefaultDict, Dict, List, Set


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Message:
    message_id: int
    conversation_id: str
    sender_id: str
    body: str
    sent_at: datetime


class ChatService:
    def __init__(self) -> None:
        self._next_message_id = 1
        self._conversations: Dict[str, Set[str]] = {}
        self._messages: DefaultDict[str, List[Message]] = defaultdict(list)
        self._presence: Set[str] = set()
        self._delivery_queues: DefaultDict[str, List[Message]] = defaultdict(list)

    def create_conversation(self, conversation_id: str, participants: Set[str]) -> None:
        self._conversations[conversation_id] = set(participants)

    def set_online(self, user_id: str) -> None:
        self._presence.add(user_id)

    def set_offline(self, user_id: str) -> None:
        self._presence.discard(user_id)

    def send_message(self, conversation_id: str, sender_id: str, body: str) -> Message:
        participants = self._conversations[conversation_id]
        if sender_id not in participants:
            raise ValueError("sender is not part of the conversation")

        message = Message(
            message_id=self._next_message_id,
            conversation_id=conversation_id,
            sender_id=sender_id,
            body=body,
            sent_at=utcnow(),
        )
        self._next_message_id += 1
        self._messages[conversation_id].append(message)

        for participant in participants:
            if participant != sender_id:
                self._delivery_queues[participant].append(message)
        return message

    def fetch_history(self, conversation_id: str, limit: int = 20) -> list[Message]:
        return self._messages[conversation_id][-limit:]

    def pull_inbox(self, user_id: str) -> list[Message]:
        queued = list(self._delivery_queues[user_id])
        self._delivery_queues[user_id].clear()
        return queued

    def presence(self, user_id: str) -> str:
        return "online" if user_id in self._presence else "offline"


def main() -> None:
    chat = ChatService()
    chat.create_conversation("c1", {"alice", "bob", "carol"})
    chat.set_online("alice")
    chat.set_online("bob")

    chat.send_message("c1", "alice", "ship the design doc")
    chat.send_message("c1", "bob", "on it")

    print("Bob inbox:")
    for message in chat.pull_inbox("bob"):
        print(f"{message.sender_id}: {message.body}")

    print()
    print("Conversation history:")
    for message in chat.fetch_history("c1"):
        print(f"{message.sender_id}: {message.body}")


if __name__ == "__main__":
    main()