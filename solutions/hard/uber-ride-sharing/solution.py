from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, List, Set, Tuple


@dataclass(slots=True)
class DriverLocation:
    driver_id: str
    lat: float
    lon: float
    available: bool = True


@dataclass(slots=True)
class RideAssignment:
    rider_id: str
    driver_id: str
    distance: float
    surge_multiplier: float


class RideSharingService:
    def __init__(self, cell_size: float = 0.02) -> None:
        self.cell_size = cell_size
        self._drivers: Dict[str, DriverLocation] = {}
        self._cells: Dict[Tuple[int, int], Set[str]] = {}
        self._zone_supply: Dict[str, int] = {}
        self._zone_demand: Dict[str, int] = {}

    def update_driver_location(self, driver_id: str, lat: float, lon: float, available: bool = True) -> None:
        previous = self._drivers.get(driver_id)
        if previous is not None:
            previous_cell = self._cell_for(previous.lat, previous.lon)
            self._cells.get(previous_cell, set()).discard(driver_id)

        location = DriverLocation(driver_id=driver_id, lat=lat, lon=lon, available=available)
        self._drivers[driver_id] = location
        cell = self._cell_for(lat, lon)
        self._cells.setdefault(cell, set()).add(driver_id)

    def request_ride(self, rider_id: str, lat: float, lon: float, zone: str) -> RideAssignment:
        self._zone_demand[zone] = self._zone_demand.get(zone, 0) + 1
        candidate_ids = self._candidate_drivers(lat, lon)
        candidates = [self._drivers[driver_id] for driver_id in candidate_ids if self._drivers[driver_id].available]
        if not candidates:
            raise ValueError("no nearby drivers available")

        best_driver = min(candidates, key=lambda driver: self._distance(lat, lon, driver.lat, driver.lon))
        best_driver.available = False
        surge_multiplier = self.surge_multiplier(zone)
        return RideAssignment(
            rider_id=rider_id,
            driver_id=best_driver.driver_id,
            distance=self._distance(lat, lon, best_driver.lat, best_driver.lon),
            surge_multiplier=surge_multiplier,
        )

    def set_zone_supply(self, zone: str, active_drivers: int) -> None:
        self._zone_supply[zone] = active_drivers

    def surge_multiplier(self, zone: str) -> float:
        demand = self._zone_demand.get(zone, 0)
        supply = max(self._zone_supply.get(zone, 1), 1)
        pressure = demand / supply
        return round(max(1.0, min(3.0, 1.0 + pressure * 0.5)), 2)

    def _candidate_drivers(self, lat: float, lon: float) -> List[str]:
        cell_x, cell_y = self._cell_for(lat, lon)
        candidates: Set[str] = set()
        for delta_x in (-1, 0, 1):
            for delta_y in (-1, 0, 1):
                candidates.update(self._cells.get((cell_x + delta_x, cell_y + delta_y), set()))
        return list(candidates)

    def _cell_for(self, lat: float, lon: float) -> tuple[int, int]:
        return int(lat / self.cell_size), int(lon / self.cell_size)

    def _distance(self, lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
        return round(sqrt((lat_a - lat_b) ** 2 + (lon_a - lon_b) ** 2), 4)


def main() -> None:
    service = RideSharingService()
    service.set_zone_supply("downtown", active_drivers=3)
    service.update_driver_location("d1", 12.9711, 77.5940)
    service.update_driver_location("d2", 12.9708, 77.5945)
    service.update_driver_location("d3", 12.9650, 77.6100)

    assignment = service.request_ride("rider-1", 12.9710, 77.5942, zone="downtown")
    print(assignment)


if __name__ == "__main__":
    main()