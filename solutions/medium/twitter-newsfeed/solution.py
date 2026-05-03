from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Set


@dataclass(slots=True)
class Tweet:
    tweet_id: int
    author_id: str
    text: str
    sequence: int


class NewsfeedService:
    def __init__(self, celebrity_threshold: int = 2) -> None:
        self.celebrity_threshold = celebrity_threshold
        self._next_tweet_id = 1
        self._sequence = 1
        self._tweets_by_user: DefaultDict[str, List[Tweet]] = defaultdict(list)
        self._followers: DefaultDict[str, Set[str]] = defaultdict(set)
        self._following: DefaultDict[str, Set[str]] = defaultdict(set)
        self._materialized_timelines: DefaultDict[str, List[Tweet]] = defaultdict(list)

    def follow(self, follower_id: str, author_id: str) -> None:
        self._following[follower_id].add(author_id)
        self._followers[author_id].add(follower_id)
        if not self._is_celebrity(author_id):
            self._materialized_timelines[follower_id].extend(self._tweets_by_user[author_id][-20:])
            self._trim_timeline(follower_id)

    def post_tweet(self, author_id: str, text: str) -> Tweet:
        tweet = Tweet(
            tweet_id=self._next_tweet_id,
            author_id=author_id,
            text=text,
            sequence=self._sequence,
        )
        self._next_tweet_id += 1
        self._sequence += 1
        self._tweets_by_user[author_id].append(tweet)

        if not self._is_celebrity(author_id):
            for follower_id in self._followers[author_id] | {author_id}:
                self._materialized_timelines[follower_id].append(tweet)
                self._trim_timeline(follower_id)
        else:
            self._materialized_timelines[author_id].append(tweet)
            self._trim_timeline(author_id)
        return tweet

    def get_timeline(self, user_id: str, limit: int = 10) -> list[Tweet]:
        candidates = list(self._materialized_timelines[user_id])
        for author_id in self._following[user_id]:
            if self._is_celebrity(author_id):
                candidates.extend(self._tweets_by_user[author_id][-20:])

        deduped: Dict[int, Tweet] = {tweet.tweet_id: tweet for tweet in candidates}
        return sorted(deduped.values(), key=lambda tweet: tweet.sequence, reverse=True)[:limit]

    def _is_celebrity(self, author_id: str) -> bool:
        return len(self._followers[author_id]) > self.celebrity_threshold

    def _trim_timeline(self, user_id: str) -> None:
        self._materialized_timelines[user_id] = self._materialized_timelines[user_id][-100:]


def main() -> None:
    service = NewsfeedService(celebrity_threshold=1)
    service.follow("alice", "bob")
    service.follow("carol", "bob")
    service.follow("alice", "dana")

    service.post_tweet("dana", "small-account update")
    service.post_tweet("bob", "celebrity post one")
    service.post_tweet("bob", "celebrity post two")

    print("Alice timeline:")
    for tweet in service.get_timeline("alice"):
        print(f"{tweet.author_id}: {tweet.text}")


if __name__ == "__main__":
    main()