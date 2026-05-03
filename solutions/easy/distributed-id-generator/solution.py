from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SnowflakeLayout:
    epoch_ms: int = 1_704_067_200_000
    datacenter_bits: int = 5
    machine_bits: int = 5
    sequence_bits: int = 12

    @property
    def machine_shift(self) -> int:
        return self.sequence_bits

    @property
    def datacenter_shift(self) -> int:
        return self.machine_bits + self.sequence_bits

    @property
    def timestamp_shift(self) -> int:
        return self.datacenter_bits + self.machine_bits + self.sequence_bits

    @property
    def max_datacenter_id(self) -> int:
        return (1 << self.datacenter_bits) - 1

    @property
    def max_machine_id(self) -> int:
        return (1 << self.machine_bits) - 1

    @property
    def max_sequence(self) -> int:
        return (1 << self.sequence_bits) - 1


class SnowflakeGenerator:
    def __init__(self, datacenter_id: int, machine_id: int, layout: SnowflakeLayout | None = None) -> None:
        self.layout = layout or SnowflakeLayout()
        if datacenter_id > self.layout.max_datacenter_id or datacenter_id < 0:
            raise ValueError("datacenter_id out of range")
        if machine_id > self.layout.max_machine_id or machine_id < 0:
            raise ValueError("machine_id out of range")

        self.datacenter_id = datacenter_id
        self.machine_id = machine_id
        self.last_timestamp_ms = -1
        self.sequence = 0

    def _current_timestamp_ms(self) -> int:
        return time.time_ns() // 1_000_000

    def _wait_for_next_millisecond(self, current_timestamp_ms: int) -> int:
        next_timestamp = self._current_timestamp_ms()
        while next_timestamp <= current_timestamp_ms:
            next_timestamp = self._current_timestamp_ms()
        return next_timestamp

    def next_id(self) -> int:
        timestamp_ms = self._current_timestamp_ms()
        if timestamp_ms < self.last_timestamp_ms:
            raise RuntimeError("clock moved backward; refusing to generate IDs")

        if timestamp_ms == self.last_timestamp_ms:
            self.sequence = (self.sequence + 1) & self.layout.max_sequence
            if self.sequence == 0:
                timestamp_ms = self._wait_for_next_millisecond(timestamp_ms)
        else:
            self.sequence = 0

        self.last_timestamp_ms = timestamp_ms
        relative_timestamp = timestamp_ms - self.layout.epoch_ms
        return (
            (relative_timestamp << self.layout.timestamp_shift)
            | (self.datacenter_id << self.layout.datacenter_shift)
            | (self.machine_id << self.layout.machine_shift)
            | self.sequence
        )

    def decode(self, identifier: int) -> dict[str, int]:
        timestamp = (identifier >> self.layout.timestamp_shift) + self.layout.epoch_ms
        datacenter_id = (identifier >> self.layout.datacenter_shift) & self.layout.max_datacenter_id
        machine_id = (identifier >> self.layout.machine_shift) & self.layout.max_machine_id
        sequence = identifier & self.layout.max_sequence
        return {
            "timestamp_ms": timestamp,
            "datacenter_id": datacenter_id,
            "machine_id": machine_id,
            "sequence": sequence,
        }


def main() -> None:
    generator = SnowflakeGenerator(datacenter_id=1, machine_id=7)
    generated_ids = [generator.next_id() for _ in range(3)]

    print("Generated Snowflake-style IDs:")
    for identifier in generated_ids:
        print(identifier)

    print()
    print("Decoded first ID:")
    print(generator.decode(generated_ids[0]))


if __name__ == "__main__":
    main()