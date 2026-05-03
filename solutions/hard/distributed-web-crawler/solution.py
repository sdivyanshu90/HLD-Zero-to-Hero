from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


@dataclass(slots=True)
class Page:
    url: str
    links: list[str]


class DistributedWebCrawler:
    def __init__(self) -> None:
        self._frontier: deque[str] = deque()
        self._seen_urls: set[str] = set()
        self._stored_pages: dict[str, Page] = {}
        self._robots_disallow: dict[str, list[str]] = {}

    def set_robots_rules(self, host: str, disallowed_prefixes: list[str]) -> None:
        self._robots_disallow[host] = disallowed_prefixes

    def schedule(self, url: str) -> None:
        canonical = self._canonicalize(url)
        if canonical in self._seen_urls:
            return
        self._seen_urls.add(canonical)
        self._frontier.append(canonical)

    def crawl_next(self, web: dict[str, list[str]]) -> str | None:
        if not self._frontier:
            return None

        url = self._frontier.popleft()
        parsed = urlparse(url)
        for disallowed_prefix in self._robots_disallow.get(parsed.netloc, []):
            if parsed.path.startswith(disallowed_prefix):
                return f"skipped robots={url}"

        links = [self._canonicalize(link) for link in web.get(url, [])]
        self._stored_pages[url] = Page(url=url, links=links)
        for link in links:
            self.schedule(link)
        return f"crawled {url} links={len(links)}"

    def stored_urls(self) -> list[str]:
        return sorted(self._stored_pages.keys())

    def _canonicalize(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = parsed._replace(fragment="", query="")
        path = normalized.path or "/"
        normalized = normalized._replace(path=path.rstrip("/") or "/")
        return urlunparse(normalized)


def main() -> None:
    crawler = DistributedWebCrawler()
    crawler.set_robots_rules("docs.example.com", ["/private"])
    crawler.schedule("https://docs.example.com/")

    mock_web = {
        "https://docs.example.com/": [
            "https://docs.example.com/guide",
            "https://docs.example.com/private/admin",
        ],
        "https://docs.example.com/guide": ["https://docs.example.com/tutorial"],
        "https://docs.example.com/tutorial": [],
    }

    while True:
        result = crawler.crawl_next(mock_web)
        if result is None:
            break
        print(result)

    print("stored:", crawler.stored_urls())


if __name__ == "__main__":
    main()