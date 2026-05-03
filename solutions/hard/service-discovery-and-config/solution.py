from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import DefaultDict, Dict, List


@dataclass(slots=True)
class ServiceInstance:
    instance_id: str
    endpoint: str
    lease_deadline: float


@dataclass(slots=True)
class ConfigChange:
    version: int
    service_name: str
    key: str
    value: str


class ServiceDiscoveryControlPlane:
    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, ServiceInstance]] = {}
        self._config_changes: list[ConfigChange] = []
        self._current_leader_term = 0

    def become_leader(self, leader_term: int) -> None:
        if leader_term <= self._current_leader_term:
            raise ValueError("leader term must increase monotonically")
        self._current_leader_term = leader_term

    def register(self, service_name: str, instance_id: str, endpoint: str, ttl_seconds: int = 10) -> None:
        service_instances = self._registry.setdefault(service_name, {})
        service_instances[instance_id] = ServiceInstance(
            instance_id=instance_id,
            endpoint=endpoint,
            lease_deadline=monotonic() + ttl_seconds,
        )

    def heartbeat(self, service_name: str, instance_id: str, ttl_seconds: int = 10) -> None:
        self._registry[service_name][instance_id].lease_deadline = monotonic() + ttl_seconds

    def discover(self, service_name: str) -> list[str]:
        self._cleanup_expired(service_name)
        return sorted(instance.endpoint for instance in self._registry.get(service_name, {}).values())

    def publish_config(self, leader_term: int, service_name: str, key: str, value: str) -> int:
        if leader_term != self._current_leader_term:
            raise ValueError("stale leader cannot publish config")
        version = len(self._config_changes) + 1
        self._config_changes.append(ConfigChange(version, service_name, key, value))
        return version

    def watch_since(self, version: int) -> list[ConfigChange]:
        return [change for change in self._config_changes if change.version > version]

    def _cleanup_expired(self, service_name: str) -> None:
        now = monotonic()
        instances = self._registry.get(service_name, {})
        for instance_id in list(instances.keys()):
            if instances[instance_id].lease_deadline <= now:
                instances.pop(instance_id, None)


def main() -> None:
    control_plane = ServiceDiscoveryControlPlane()
    control_plane.become_leader(leader_term=1)
    control_plane.register("timeline", "i-1", "10.0.0.1:8080")
    control_plane.register("timeline", "i-2", "10.0.0.2:8080")
    version = control_plane.publish_config(1, "timeline", "timeout_ms", "250")

    print("discovered endpoints:", control_plane.discover("timeline"))
    print("config version:", version)
    print("watch changes:", control_plane.watch_since(0))


if __name__ == "__main__":
    main()