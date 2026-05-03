# TCP vs UDP

## Core Difference

TCP (Transmission Control Protocol) provides **reliable, ordered, connection-oriented** delivery. UDP (User Datagram Protocol) provides **best-effort, connectionless** delivery.

```
┌──────────────────────────────────────────────────────────────────┐
│                         TCP vs UDP                                │
│                                                                    │
│  TCP                              UDP                             │
│  ─────────────────────────        ─────────────────────────       │
│  Connection-oriented              Connectionless                  │
│  3-way handshake required         No setup — fire and forget      │
│  Ordered delivery                 No ordering guarantee           │
│  Retransmission on loss           No retransmission               │
│  Flow control (backpressure)      No flow control                 │
│  Congestion control               No congestion control           │
│  ~40 byte header overhead         ~8 byte header overhead         │
│  Full duplex                      Full duplex                     │
│                                                                    │
│  Suitable for:                    Suitable for:                   │
│  HTTP, databases, file transfer   Video streaming, DNS, gaming    │
│  email, SSH, HTTPS                VoIP, multicast, sensor data    │
└──────────────────────────────────────────────────────────────────┘
```

---

## TCP Deep Dive

### Reliability Mechanisms

```
TCP Sequence Numbers and ACKs:

Sender                          Receiver
  │── Seq=100, Data="Hello" ──▶│
  │── Seq=105, Data="World" ──▶│
  │                            │ (packet "World" arrives first!)
  │                            │ Receiver buffers out-of-order packet
  │◀── ACK=105 ────────────────│  "I got up to 104, missing 105"
  │── Retransmit Seq=105 ─────▶│
  │◀── ACK=110 ────────────────│  "Got all up to 109, give me 110"
```

### TCP Slow Start and Congestion Control

TCP starts conservatively and probes the network:

```
cwnd (congestion window) growth:

Packets │                    ╭──── congestion avoidance (linear)
sent    │               ╭────
per RTT │          ╭────
        │     ╭────     ← slow start (exponential: 1,2,4,8,16...)
        │ ╭───
        └──────────────────────────────────────────────▶ time
          RTT1 RTT2 RTT3 RTT4 RTT5

Packet loss detected → window halved (multiplicative decrease)
→ This is why new TCP connections are slow to ramp up throughput
→ Why HTTP/2 multiplexing over one connection is better than many small connections
```

### TCP Head-of-Line (HOL) Blocking

```
HTTP/1.1 (TCP, multiple connections):
  Stream 1: request ──▶ response
  Stream 2: request ──▶ response (waits for stream 1 to finish)

HTTP/2 (TCP, single multiplexed connection):
  Stream 1: [HEADERS] [DATA frame] [DATA frame]
  Stream 2: [HEADERS] [DATA frame]            ← interleaved
  Stream 3: [HEADERS]

BUT: if a TCP packet is lost, ALL streams stall waiting for retransmission
  → TCP-level HOL blocking still applies to HTTP/2

HTTP/3 (QUIC/UDP, per-stream reliability):
  Packet lost in Stream 1 → only Stream 1 stalls
  Streams 2 and 3 continue unaffected
  → Eliminates HOL blocking at the transport layer
```

---

## UDP Deep Dive

### Why Not Always TCP?

```
Video call scenario (real-time):

With TCP:
  Frame 1 (100ms ago) lost → TCP stalls, retransmits
  Frames 2, 3, 4, 5 buffered, waiting
  User sees: 500ms freeze, then all frames at once → unwatchable

With UDP (application-level handling):
  Frame 1 lost → skip it! Show slightly degraded video
  Frames 2, 3, 4, 5 displayed in real time
  User sees: momentary artifact → tolerable

Key insight: for real-time media, stale data is WORSE than missing data
```

### UDP Use Cases

| Application | Why UDP | What Handles Loss |
|-------------|---------|-------------------|
| DNS | Speed (1 packet = 1 query+response) | Client retries on timeout |
| Video call (WebRTC) | Real-time, old frames useless | App-level FEC, interpolation |
| Online gaming | Low latency positional updates | Game state reconciliation |
| DHCP | Bootstrapping (no IP yet) | Retries |
| NTP | Single packet time sync | Retries |
| Multicast streaming | One packet to N receivers | FEC codes |
| QUIC (HTTP/3) | Custom reliability per stream | QUIC's own reliability layer |

---

## QUIC: The Best of Both Worlds

QUIC is a protocol built on UDP that reimplements TCP's reliability features but solves TCP's HOL blocking problem:

```
┌──────────────────────────────────────────────────────────────────┐
│                         QUIC ARCHITECTURE                         │
│                                                                    │
│   Application Layer:    HTTP/3 (streams)                          │
│   ──────────────────────────────────────────────────────────      │
│   QUIC Layer:           Reliability per stream, flow control      │
│                         0-RTT/1-RTT handshake, connection ID      │
│   ──────────────────────────────────────────────────────────      │
│   TLS 1.3:              Always encrypted (no plaintext QUIC)      │
│   ──────────────────────────────────────────────────────────      │
│   UDP:                  Unreliable datagram transport             │
└──────────────────────────────────────────────────────────────────┘

QUIC advantages over TCP+TLS:
  TCP+TLS 1.3:  1.5 RTT (TCP) + 1 RTT (TLS) = 2.5 RTT to first byte
  QUIC (new):   1 RTT to first byte (0-RTT for known servers!)
  QUIC (0-RTT): 0 RTT data with session resumption (slight security trade-off)

  Connection migration: QUIC connections survive IP change (mobile, WiFi switch)
  TCP connections die when IP changes (e.g., phone moves from WiFi to LTE)
```

---

## Choosing TCP vs UDP

```
Decision Framework:

                    Does loss matter?
                         │
               ┌─────────┴─────────┐
               Yes                 No
               │                   │
    ┌──────────▼─────┐    ┌────────▼────────────┐
    │Does order matter│    │ Real-time/low lat?  │
    └──────────┬──────┘    └────────┬────────────┘
               │                   │
         ┌─────▼──────┐    ┌───────▼────────┐
         │    TCP     │    │     UDP        │
         │ (or QUIC)  │    │ (app handles   │
         └────────────┘    │   reliability) │
                           └────────────────┘

Examples:
  HTTP APIs, databases, file transfer → TCP
  Video calls, game state, DNS        → UDP
  Browser HTTP/3                      → QUIC (UDP-based)
```

---

## Interview Quick Answers

- **Why does Kafka use TCP?** — Durability and ordering guarantees are critical; replication must be reliable.
- **Why does DNS use UDP?** — Single small request+response fits in one datagram; no connection overhead; client retries on timeout.
- **Why does WebRTC use UDP?** — Real-time video; a retransmitted frame would arrive after it's useful; better to skip than delay.
- **What is HOL blocking?** — TCP must deliver packets in order; a lost packet stalls all subsequent data even if already received. QUIC solves this per-stream.
