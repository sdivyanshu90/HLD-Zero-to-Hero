# Authentication and Transport Security

Distributed systems need both identity and secure transport.

## mTLS

Mutual TLS authenticates both client and server certificates.

## OAuth 2.0

OAuth 2.0 delegates authorization and issues tokens for protected resource access.

## JWT

JSON Web Tokens carry signed claims that let systems perform stateless auth checks.

## Real-World Analogy

mTLS is both sides showing official badges, OAuth 2.0 is a delegated permission slip, and JWT is a signed pass that many guards can verify.

## Trade-Offs

- mTLS improves service-to-service trust but complicates certificate management.
- OAuth 2.0 is flexible but complex.
- JWT reduces lookup cost but makes revocation and claim freshness harder.

## Interview Use

Separate transport security from authorization. They solve different problems.
