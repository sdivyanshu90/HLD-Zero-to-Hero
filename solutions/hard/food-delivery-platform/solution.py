from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, List, Tuple


@dataclass(slots=True)
class Courier:
    courier_id: str
    lat: float
    lon: float
    available: bool = True


@dataclass(slots=True)
class Order:
    order_id: str
    customer_id: str
    restaurant_id: str
    items: list[str]
    total_cents: int
    state: str = "created"
    courier_id: str | None = None


class FoodDeliveryPlatform:
    def __init__(self) -> None:
        self._menus: Dict[str, List[str]] = {}
        self._orders: Dict[str, Order] = {}
        self._couriers: Dict[str, Courier] = {}

    def set_menu(self, restaurant_id: str, items: list[str]) -> None:
        self._menus[restaurant_id] = list(items)

    def register_courier(self, courier_id: str, lat: float, lon: float) -> None:
        self._couriers[courier_id] = Courier(courier_id, lat, lon)

    def place_order(self, order_id: str, customer_id: str, restaurant_id: str, items: list[str], total_cents: int) -> None:
        menu = set(self._menus[restaurant_id])
        if any(item not in menu for item in items):
            raise ValueError("order contains unavailable menu items")
        self._orders[order_id] = Order(order_id, customer_id, restaurant_id, items, total_cents, state="payment_authorized")

    def accept_order(self, order_id: str) -> None:
        self._orders[order_id].state = "accepted"

    def assign_courier(self, order_id: str, pickup_lat: float, pickup_lon: float) -> str:
        available = [courier for courier in self._couriers.values() if courier.available]
        if not available:
            raise ValueError("no couriers available")
        best = min(available, key=lambda courier: self._distance(courier.lat, courier.lon, pickup_lat, pickup_lon))
        best.available = False
        order = self._orders[order_id]
        order.courier_id = best.courier_id
        order.state = "courier_assigned"
        return best.courier_id

    def mark_delivered(self, order_id: str) -> None:
        order = self._orders[order_id]
        order.state = "delivered"
        if order.courier_id is not None:
            self._couriers[order.courier_id].available = True

    def order_status(self, order_id: str) -> str:
        return self._orders[order_id].state

    def _distance(self, lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
        return sqrt((lat_a - lat_b) ** 2 + (lon_a - lon_b) ** 2)


def main() -> None:
    platform = FoodDeliveryPlatform()
    platform.set_menu("r1", ["pizza", "pasta", "salad"])
    platform.register_courier("c1", 12.97, 77.59)
    platform.register_courier("c2", 12.98, 77.61)

    platform.place_order("o1", "u1", "r1", ["pizza"], total_cents=1499)
    platform.accept_order("o1")
    courier_id = platform.assign_courier("o1", pickup_lat=12.971, pickup_lon=77.594)
    platform.mark_delivered("o1")

    print("assigned courier:", courier_id)
    print("order status:", platform.order_status("o1"))


if __name__ == "__main__":
    main()