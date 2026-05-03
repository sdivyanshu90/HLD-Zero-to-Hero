# Cheat Sheet: Payment Ledger Platform

## Scale (BoE)
```
Transactions per day: 100M
Transaction QPS: 100M / 86,400 ≈ 1,160 TPS average, 5K TPS peak
Transaction size: ~500 bytes
Daily storage: 100M × 500 bytes = 50 GB/day → ~18 TB/year
Idempotency requirement: must never double-charge
Audit trail: every transaction must be immutable and queryable
```

## Double-Entry Bookkeeping

```
Every financial transaction creates TWO entries:
  Debit one account, Credit another (always balanced)
  
  Alice pays Bob $100:
  ┌─────────────────────────────────────────────┐
  │ Transaction: txn_001                         │
  │ Debit:  Alice checking  -$100               │
  │ Credit: Bob checking    +$100               │
  │                                             │
  │ Sum of all entries = 0 (conservation law)   │
  └─────────────────────────────────────────────┘
  
  Schema:
    accounts: (id, user_id, currency, balance)
    ledger_entries: (txn_id, account_id, amount, type, created_at)
    
    balance = SUM(amount) for all entries for account_id
    (Or: maintain running balance + append entries)
```

## Idempotency

```
Challenge: Alice's payment times out. Did it go through?
  → Client retries → double charge!
  
Solution: Idempotency Key
  Client generates unique payment_id (UUID) before attempting
  Server: INSERT INTO payments (payment_id, ...) ON CONFLICT (payment_id) DO NOTHING
  If INSERT affected 0 rows: return cached result → no double charge
  
  Process:
    1. Client sends payment with payment_id=uuid-123
    2. Server checks: seen payment_id=uuid-123? No → proceed
    3. Charge card → SUCCESS
    4. Record: payment_id=uuid-123, result=SUCCESS, amount=$100
    5. On retry: check → seen uuid-123 → return SUCCESS (no re-charge)
    6. On network timeout: retry with same uuid-123 → safe
```

## ACID Transactions

```
Payment must be atomic (all-or-nothing):
  BEGIN TRANSACTION
  
  SELECT balance FROM accounts WHERE id = 'alice' FOR UPDATE;  -- lock alice
  SELECT balance FROM accounts WHERE id = 'bob' FOR UPDATE;    -- lock bob
  
  IF alice.balance < 100: ROLLBACK; RAISE insufficient_funds
  
  INSERT INTO ledger_entries (txn_id, account_id, amount, type)
    VALUES (uuid, 'alice', -100, 'DEBIT'),
           (uuid, 'bob',   +100, 'CREDIT');
  
  UPDATE accounts SET balance = balance - 100 WHERE id = 'alice';
  UPDATE accounts SET balance = balance + 100 WHERE id = 'bob';
  
  COMMIT;
  
  This uses PostgreSQL with SERIALIZABLE isolation.
```

## Bottlenecks
1. Write throughput: 5K TPS → PostgreSQL can handle 1-10K TPS → need to shard by account_id range
2. Hot account: heavily trafficked account (e.g., Amazon's merchant account) → row lock contention
   → Solution: aggregate to intermediate account nodes, batch settlements

## Unique Trick
Immutable ledger: never UPDATE or DELETE ledger entries. If a payment is reversed: add a compensating entry (credit Alice, debit Bob). The ledger is append-only and auditable — you can replay from the beginning to reconstruct any balance at any point in time.
