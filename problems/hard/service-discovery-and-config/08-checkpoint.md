# Step 8 — Checkpoint & Interview Q&A

**Q1: Why is service discovery a CP system (not AP)?**
> If two nodes disagree on which service instances are healthy (partition), routing traffic to a stale list can cause cascade failures. It's better to return an error ("can't determine healthy instances") than to route to potentially dead servers. Consul uses Raft — a minority partition refuses to serve queries rather than return stale data.

**Q2: How does a service know when another service's config changes?**
> Long-polling (Consul) or gRPC watch stream (etcd). Services send a blocking GET with the last-seen index. When config changes, the server unblocks and returns the new value. Client immediately applies the change and opens a new watch. Propagation latency: < 1 second to all watchers globally.

**Q3: How do you detect and remove failed service instances?**
> Health checks: (1) HTTP: registry calls GET /health every 10s; failure after 3 consecutive misses = deregister. (2) TTL: service must call PUT /agent/check/pass every 15s; if TTL expires → unhealthy. (3) TCP: registry opens TCP connection; failure = port closed. Deregistration triggers watch events → all consumers get updated service list.

**Q4: How do you elect a new leader after the current one fails?**
> Raft election: all followers have a randomized election timeout (150-300ms). First one to time out sends RequestVote to others. Majority vote (quorum) wins and becomes leader. New leader starts a new term. Total election time: ~300ms. During election, cluster refuses writes (CP guarantee).

**Q5: How do you roll out a config change to 10,000 services safely?**
> (1) Write config to etcd. (2) All services have a watch → get notified within 1-2s. (3) Services apply change via hot-reload (no restart). (4) Canary: use feature flags — change config key only for services with tag "canary=true" first. (5) Rollback: re-write old value to etcd; all services revert within 2s.
