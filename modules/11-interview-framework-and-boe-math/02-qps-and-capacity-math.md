# QPS and Capacity Math

Quick request math prevents hand-wavy design decisions.

## Core Shortcut

One million requests per day is about 11.6 requests per second, which people round to about 12 QPS.

## Why It Matters

Daily numbers sound large, but QPS exposes the real intensity the system must sustain.

## Useful Conversions

- 10M per day is about 116 QPS
- 100M per day is about 1,160 QPS

## Interview Use

Convert daily numbers into per-second numbers before choosing instance count, cache size, or database topology.
