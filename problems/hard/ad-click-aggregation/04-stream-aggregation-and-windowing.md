# Step 4 — Stream Aggregation and Windowing

## Window Types

```
Tumbling Window (non-overlapping):
  ├──── 10:00-10:01 ────┤├──── 10:01-10:02 ────┤
  Use: Billing per minute, hourly reports

Sliding Window (overlapping):
  [10:00-10:05] [10:01-10:06] [10:02-10:07]
  Use: Moving average, anomaly detection

Session Window (activity-based):
  User active: |--click--pause(>5min)--|  → session ends
  Use: User session analytics
```

## Flink Tumbling Window Example

```java
DataStream<ClickEvent> clicks = env.addSource(kafkaSource);

clicks
  .keyBy(click -> click.getAdId())
  .window(TumblingEventTimeWindows.of(Time.minutes(1)))
  .aggregate(new ClickCountAggregator())
  .addSink(clickhouseSink);

class ClickCountAggregator implements AggregateFunction<ClickEvent, Long, AggResult> {
    public Long createAccumulator() { return 0L; }
    public Long add(ClickEvent ev, Long acc) { return acc + 1; }
    public AggResult getResult(Long acc) { return new AggResult(acc); }
    public Long merge(Long a, Long b) { return a + b; }
}
```

## Watermarks for Event-Time Processing

```
Problem: Events arrive out of order (network delays, mobile offline)

Watermark = "I've seen all events up to timestamp T"
  → triggers window close when watermark passes window end time
  → handles late events up to allowed lateness

Watermark strategy:
  WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofMinutes(1))
  → window [10:00-10:01] fires at 10:02 (allowing 1 min lateness)
  → events arriving after 10:02 for that window → side output (late data)
```

## Aggregation State in Flink

```
Flink uses RocksDB as state backend for large state:
  State per key (ad_id): {count: 142, unique_users: HashSet}
  Checkpointed to S3 every 60s (fault tolerance)
  
Memory estimate:
  100K active ads × 100B state per key = 10 MB (trivial)
  But unique_users set can be large → use HyperLogLog for cardinality
```
