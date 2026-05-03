# Step 4 — Ledger Storage and Double-Entry Bookkeeping

## Double-Entry Principle

```
Every financial transaction = 2 entries that sum to zero
  Debit  one account  (money leaves)
  Credit another account (money arrives)

Transfer $100 from Alice to Bob:
  Entry 1: DEBIT  alice_account  $100  (alice's balance ↓)
  Entry 2: CREDIT bob_account    $100  (bob's balance ↑)

Sum of all entries = 0  (conservation law — no money created/destroyed)
```

## Ledger Schema

```sql
CREATE TABLE accounts (
    account_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      BIGINT NOT NULL,
    account_type VARCHAR(32) NOT NULL,  -- checking, savings, liability
    currency     CHAR(3) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ledger_entries (
    entry_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    txn_id        UUID NOT NULL,    -- groups debit+credit pair
    account_id    UUID NOT NULL REFERENCES accounts(account_id),
    amount        NUMERIC(18, 2) NOT NULL,  -- positive or negative
    direction     CHAR(6) NOT NULL,         -- DEBIT or CREDIT
    balance_after NUMERIC(18, 2) NOT NULL,  -- running balance snapshot
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description   TEXT
);

CREATE INDEX ON ledger_entries(account_id, created_at DESC);
CREATE INDEX ON ledger_entries(txn_id);

-- Idempotency
CREATE TABLE payment_requests (
    idempotency_key VARCHAR(256) PRIMARY KEY,
    txn_id          UUID,
    status          VARCHAR(16),  -- pending, completed, failed
    created_at      TIMESTAMPTZ
);
```

## Transfer Transaction

```sql
-- Atomic double-entry transfer (SERIALIZABLE isolation)
BEGIN;

-- Idempotency check
INSERT INTO payment_requests (idempotency_key, status, created_at)
VALUES ('pay_abc123', 'pending', NOW())
ON CONFLICT (idempotency_key) DO NOTHING;

-- If idempotency key already existed → check status and return early
SELECT txn_id, status FROM payment_requests WHERE idempotency_key = 'pay_abc123';

-- If status = completed → return existing txn_id (idempotent success)
-- If status = pending → another request in flight → wait or return conflict

-- Generate transaction ID
INSERT INTO transactions (txn_id, from_account, to_account, amount)
VALUES ('txn_xyz', 'alice_acct', 'bob_acct', 100.00);

-- Debit Alice
INSERT INTO ledger_entries (txn_id, account_id, amount, direction, balance_after)
VALUES ('txn_xyz', 'alice_acct', -100.00, 'DEBIT',
        (SELECT balance_after FROM ledger_entries
         WHERE account_id = 'alice_acct' ORDER BY created_at DESC LIMIT 1) - 100.00);

-- Credit Bob
INSERT INTO ledger_entries (txn_id, account_id, amount, direction, balance_after)
VALUES ('txn_xyz', 'bob_acct', 100.00, 'CREDIT',
        (SELECT balance_after FROM ledger_entries
         WHERE account_id = 'bob_acct' ORDER BY created_at DESC LIMIT 1) + 100.00);

-- Mark idempotency key as completed
UPDATE payment_requests SET status='completed', txn_id='txn_xyz'
WHERE idempotency_key = 'pay_abc123';

COMMIT;
```

## Why SERIALIZABLE Isolation?

```
Balance check + update must be atomic:
  READ COMMITTED: two concurrent transfers from Alice both see balance = $100
    Both succeed → Alice ends up with -$100 (overdraft)
  SERIALIZABLE: one transaction wins; other retries
    Correct behavior guaranteed

PostgreSQL SERIALIZABLE: uses predicate locks (SSI algorithm)
  Low overhead for read-heavy workloads
  Automatic retry on serialization failure:
    SQLSTATE 40001 → application retries transaction
```
