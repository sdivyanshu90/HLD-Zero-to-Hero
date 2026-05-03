# Circuit Breakers and Bulkheads

## Cascading Failures

Without resilience patterns, one slow service can bring down your entire system:

```
Request path:
  Client → API Gateway → Order Service → Payment Service (SLOW!)
  
  Payment Service gets slow (DB overload, memory pressure)
  Order Service requests pile up waiting for Payment response
  Order Service thread pool fills up → Order Service hangs
  API Gateway requests to Order Service pile up
  All threads blocked waiting → API Gateway unresponsive
  All users get 503 errors
  
  One service's slowness → entire system down (cascade failure)
```

---

## Circuit Breaker Pattern

Modeled after electrical circuit breakers: automatically cut the connection to a failing service:

```
Circuit Breaker States:

  CLOSED (normal operation)
  ├── Requests pass through to downstream service
  ├── Track failure rate (errors / total requests)
  └── If failure rate > threshold: → OPEN

  OPEN (short-circuit)
  ├── Immediately reject requests (no waiting for timeout)
  ├── Return fallback response or error
  └── After timeout period: → HALF-OPEN

  HALF-OPEN (testing)
  ├── Allow a small number of probe requests through
  ├── If probe succeeds: → CLOSED (service recovered)
  └── If probe fails: → OPEN (still failing)

State transitions:
  CLOSED → OPEN: failure rate > 50% over last 10 requests (or last 60s window)
  OPEN → HALF-OPEN: after 30 second sleep window
  HALF-OPEN → CLOSED: 3 consecutive successes
  HALF-OPEN → OPEN: any failure

Benefits:
  ✓ Fail fast: instead of blocking for 30s timeout, fail immediately
  ✓ Protects downstream: open circuit stops additional load on failing service
  ✓ Automatic recovery: half-open probes test recovery without full load
```

### Circuit Breaker Implementation

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, success_threshold=2, timeout=30):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout  # seconds in OPEN state before HALF-OPEN
        self.state = "CLOSED"
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None
    
    def call(self, func, *args):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF-OPEN"
                self.successes = 0
            else:
                raise CircuitOpenException("Circuit is OPEN")  # fail fast!
        
        try:
            result = func(*args)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        if self.state == "HALF-OPEN":
            self.successes += 1
            if self.successes >= self.success_threshold:
                self.state = "CLOSED"
                self.failures = 0
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

# Libraries: Resilience4j (Java), Polly (.NET), Hystrix (Java, maintenance mode)
```

---

## Bulkhead Pattern

Isolate components so failure in one doesn't exhaust resources for others:

```
Without bulkhead: shared thread pool
  ┌────────────────────────────────────────┐
  │  API Server (20 threads total)          │
  │                                         │
  │  10 threads blocked on slow PaymentSvc  │
  │  5 threads blocked on slow InventorySvc │
  │  5 threads left for everything else     │
  │  → System almost unavailable!           │
  └────────────────────────────────────────┘

With bulkhead: isolated thread pools per dependency
  ┌────────────────────────────────────────┐
  │  API Server                             │
  │  ┌──────────┐  ┌──────────┐  ┌──────┐  │
  │  │ Payment  │  │Inventory │  │ User │  │
  │  │ Pool:5   │  │ Pool:5   │  │Pool:5│  │
  │  └──────────┘  └──────────┘  └──────┘  │
  │  PaymentSvc slow: only 5 threads blocked│
  │  InventorySvc, UserSvc still responsive │
  └────────────────────────────────────────┘

Types of bulkheads:
  1. Thread pool isolation (above)
  2. Connection pool isolation: separate DB connection pools per service
  3. Process isolation: separate process/container per component (k8s pods)
  4. Physical isolation: separate hosts per critical service
```

---

## Timeout and Retry

```
Timeout:
  Every network call MUST have a timeout
  Without timeout: hung request holds thread forever → thread pool exhaustion
  
  Timeout hierarchy:
    Connect timeout: how long to wait for TCP handshake (100ms)
    Read timeout: how long to wait for response once connected (2000ms)
    Total deadline: end-to-end time for the whole operation (5000ms)
  
  Aggressive timeouts are better:
    P99 latency of Payment Service = 300ms
    Set timeout = 500ms (P99 * 1.67 buffer)
    If 50% of requests time out → circuit breaker trips → fail fast

Retry with backoff:
  Only retry idempotent operations (GET, not POST)
  Only retry transient failures (500, timeout, not 400/401/403/404)
  Exponential backoff + jitter (see Module 09)
  
  Retry + Circuit Breaker together:
    First: retry with backoff (handles transient flakes)
    If retry fails: circuit breaker increments failure count
    If too many failures: circuit opens → no more retries → fast fail
```

---

## Interview Quick Answers

- **What are the three states of a circuit breaker?** — CLOSED (requests pass through, failures counted), OPEN (fast-fail all requests, no calls to downstream, wait for timeout), HALF-OPEN (allow limited probe requests, if they succeed → close, if they fail → reopen).
- **What is the difference between circuit breaker and bulkhead?** — Circuit breaker: detects downstream service failure and stops sending requests (temporal isolation). Bulkhead: prevents one slow dependency from consuming all thread/connection resources (resource isolation). They are complementary and often used together.
- **What timeout should you set for a service call?** — Based on the P99 latency of the dependency with some buffer (e.g., P99 × 1.5-2). Too tight = too many false timeouts. Too loose = threads blocked too long. Always set both connect timeout (short, 50-100ms) and read timeout separately.
