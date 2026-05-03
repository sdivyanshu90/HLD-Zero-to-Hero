from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(slots=True)
class LedgerEntry:
    transfer_id: str
    account_id: str
    direction: str
    amount_cents: int
    currency: str


class PaymentLedger:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._balances: Dict[str, int] = {}
        self._idempotency_index: Dict[str, str] = {}
        self._next_transfer_id = 1

    def post_transfer(
        self,
        *,
        idempotency_key: str,
        source_account: str,
        destination_account: str,
        amount_cents: int,
        currency: str,
    ) -> str:
        if idempotency_key in self._idempotency_index:
            return self._idempotency_index[idempotency_key]

        transfer_id = f"t{self._next_transfer_id}"
        self._next_transfer_id += 1
        debit = LedgerEntry(transfer_id, source_account, "debit", amount_cents, currency)
        credit = LedgerEntry(transfer_id, destination_account, "credit", amount_cents, currency)
        self._entries.extend([debit, credit])
        self._balances[source_account] = self._balances.get(source_account, 0) - amount_cents
        self._balances[destination_account] = self._balances.get(destination_account, 0) + amount_cents
        self._idempotency_index[idempotency_key] = transfer_id
        return transfer_id

    def balance(self, account_id: str) -> int:
        return self._balances.get(account_id, 0)

    def entries_for_transfer(self, transfer_id: str) -> list[LedgerEntry]:
        return [entry for entry in self._entries if entry.transfer_id == transfer_id]


def main() -> None:
    ledger = PaymentLedger()
    transfer_id = ledger.post_transfer(
        idempotency_key="req-1",
        source_account="merchant:cash",
        destination_account="platform:settlement",
        amount_cents=25_00,
        currency="USD",
    )
    duplicate = ledger.post_transfer(
        idempotency_key="req-1",
        source_account="merchant:cash",
        destination_account="platform:settlement",
        amount_cents=25_00,
        currency="USD",
    )

    print("transfer id:", transfer_id)
    print("duplicate transfer id:", duplicate)
    print("balances:", {"merchant:cash": ledger.balance("merchant:cash"), "platform:settlement": ledger.balance("platform:settlement")})
    print("entries:", ledger.entries_for_transfer(transfer_id))


if __name__ == "__main__":
    main()