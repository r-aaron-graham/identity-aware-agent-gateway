# Identity-Aware Agent Gateway Architecture

## Design goal

Show that identity is not only for authentication. Identity should shape retrieval scope, tool permissions, review thresholds, and audit records.

## Core components

- **Bearer token verifier**: validates signed identity claims
- **Identity resolver**: derives role and permission envelope
- **Policy engine**: decides whether the request is approved, clarified, reviewed, downgraded, or refused
- **Retrieval service**: filters candidate documents by classification
- **Tool executor**: only runs tools allowed for the current role
- **Workflow orchestrator**: writes requests, retrieved sources, audit events, and review items
- **Review queue**: holds privileged or out-of-scope actions for human resolution

## Why this matters

An AI agent without identity-aware boundaries is not an enterprise system. It is a powerful interface with unclear authority.
