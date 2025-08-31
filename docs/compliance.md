# Compliance Module

This module introduces basic primitives for FDA 21 CFR Part 11 and GMP workflows.

## Electronic Signatures
- Captures user intent and timestamp.
- Generates a tamper-evident hash chain for each signature.

## Electronic Batch Records
- Stores lot numbers and manufacturing descriptions.
- Links to non-conformance records for quality events.

## Non-Conformance Tracking
- Records deviations with open/closed status.

Endpoints are exposed under `/api/compliance/*` and require authenticated users with the `auditor` role.
