# Bandwidth Estimation

Bandwidth math answers whether the network, not the database, is your real bottleneck.

## Basic Formula

`bandwidth per second = requests per second × bytes per response`

## Example

If you serve 5,000 requests per second and each response is 200 KB, then outbound traffic is about:

- `5,000 × 200 KB = 1,000,000 KB/s`
- about `1 GB/s`

## Interview Use

Use this to justify CDNs, compression, image resizing, or streaming chunk design.
