from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Seat:
    seat_id: str
    state: str = "available"
    reservation_id: str | None = None


@dataclass(slots=True)
class Reservation:
    reservation_id: str
    user_id: str
    seat_ids: list[str]
    expires_at: datetime
    status: str = "reserved"


class TicketBookingSystem:
    def __init__(self, seat_ids: list[str]) -> None:
        self._seats: Dict[str, Seat] = {seat_id: Seat(seat_id=seat_id) for seat_id in seat_ids}
        self._reservations: Dict[str, Reservation] = {}
        self._next_reservation_id = 1

    def cleanup_expired_reservations(self) -> None:
        for reservation in list(self._reservations.values()):
            if reservation.status == "reserved" and utcnow() >= reservation.expires_at:
                self.cancel(reservation.reservation_id)

    def reserve(self, user_id: str, seat_ids: list[str], ttl_seconds: int = 300) -> str:
        self.cleanup_expired_reservations()
        seats = [self._seats[seat_id] for seat_id in seat_ids]
        if any(seat.state != "available" for seat in seats):
            raise ValueError("one or more seats are unavailable")

        reservation_id = f"r{self._next_reservation_id}"
        self._next_reservation_id += 1
        expires_at = utcnow() + timedelta(seconds=ttl_seconds)
        reservation = Reservation(
            reservation_id=reservation_id,
            user_id=user_id,
            seat_ids=seat_ids,
            expires_at=expires_at,
        )
        self._reservations[reservation_id] = reservation

        for seat in seats:
            seat.state = "reserved"
            seat.reservation_id = reservation_id

        return reservation_id

    def confirm(self, reservation_id: str) -> None:
        reservation = self._reservations[reservation_id]
        if utcnow() >= reservation.expires_at:
            self.cancel(reservation_id)
            raise ValueError("reservation expired before confirmation")

        reservation.status = "confirmed"
        for seat_id in reservation.seat_ids:
            seat = self._seats[seat_id]
            seat.state = "sold"

    def cancel(self, reservation_id: str) -> None:
        reservation = self._reservations[reservation_id]
        if reservation.status == "cancelled":
            return

        reservation.status = "cancelled"
        for seat_id in reservation.seat_ids:
            seat = self._seats[seat_id]
            if seat.state == "reserved" and seat.reservation_id == reservation_id:
                seat.state = "available"
                seat.reservation_id = None

    def seat_map(self) -> Dict[str, str]:
        return {seat_id: seat.state for seat_id, seat in self._seats.items()}


def main() -> None:
    system = TicketBookingSystem(seat_ids=["A-1", "A-2", "A-3"])
    reservation_id = system.reserve("u123", ["A-1", "A-2"], ttl_seconds=60)
    print("Reserved:", reservation_id)
    print("Seat map after reserve:", system.seat_map())
    system.confirm(reservation_id)
    print("Seat map after confirm:", system.seat_map())


if __name__ == "__main__":
    main()