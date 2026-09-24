# Rate limiting public API

Date: <today's date, if known>

## Context

The public `/v1/notes` endpoints have no rate limiting; one integration hammered them last week.

## Decision

Token bucket per API key, 60 req/min, enforced in the edge middleware.

## Implementation notes

- Return 429 with a `Retry-After` header.
