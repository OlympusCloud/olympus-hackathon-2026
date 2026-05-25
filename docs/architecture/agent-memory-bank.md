# Agent Memory Bank — tenant isolation contract

**Status**: shipping as the H6 deliverable for the Google Cloud for Startups Hackathon 2026 submission.
**Owners**: NebusAI / Olympus Cloud — Platform & SDK agent.
**Tracking**: parent epic `OlympusCloud/olympus-cloud-gcp#4797`; this doc closes `#4803 ac-1` and `#4803 ac-2`.
**Last verified live**: 2026-05-24 — see [`demo/memory-isolation-proof.txt`](../../demo/memory-isolation-proof.txt) for the end-to-end run output against the deployed Ceres reasoning engine in `olympuscloud-dev`.

## What Agent Memory Bank gives us

Vertex AI Agent Engine ships per-`user_id` persistent memory. Every session created with `agent_engine.create_session(user_id=...)` is structurally keyed on that user_id; sessions for one `user_id` are not visible to listing or query calls made on behalf of another `user_id`. Agent Memory Bank (the long-term-recall surface built on top of session memory) inherits the same scoping.

That gives us a single substrate-native primitive for tenant isolation — **but only if we encode `tenant_id` into the `user_id` we pass at the boundary**. The rest of this doc defines that encoding as a contract and the runtime guard that enforces it.

## The contract

Every call site that talks to Vertex AI Agent Engine MUST pass a user_id of the form:

```
"{tenant_id}:{user_id}"
```

- `tenant_id` and `user_id` are each ASCII slugs: `[A-Za-z0-9_-]+`.
- The colon (`:`) is the ONLY separator between segments. Either segment containing a colon, an empty segment, or a non-slug character is a contract violation.
- The contract is one-way intentional: a user_id without the tenant prefix is invalid; a user_id with more than one separator (`a:b:c`) is also invalid (decomposition would be ambiguous).
- Tenant ids and demo ids in this carve-out are `demo-tenant-a` / `demo-tenant-b` / `isolation-proof-user`. Production tenants follow the same shape.

The contract is defined and exported by [`adk/agent/tenant_user_id.py`](../../adk/agent/tenant_user_id.py):

| Function | Use |
|---|---|
| `scoped_user_id(tenant_id, user_id) -> str` | Build a wire-ready user_id from its two parts. Validates both segments. |
| `parse_scoped_user_id(raw) -> ScopedUserId` | Split a wire user_id back into a typed `(tenant_id, user_id)` tuple. |
| `require_scoped_user_id(raw) -> ScopedUserId` | The runtime guard. Wrap every Vertex AI Agent Engine user_id at the boundary. Raises `TenantPrefixError` on any contract violation so the caller fails fast. |

## Why this design (rather than the obvious alternative)

The simpler design — "let the agent see tenant_id from session state and filter inside its tool calls" — is **not safe**: the agent's tool implementations are not in the trust boundary. If a tool function forgets to filter, leaks happen invisibly.

The contract here pushes the isolation guarantee down into the substrate (Vertex AI Agent Engine session/memory APIs), so a forgetful tool implementation cannot violate it. The only way to violate isolation is to call the substrate without the prefix — and `require_scoped_user_id` rejects that at the call site.

## Where the contract is enforced

| Layer | Enforcement |
|---|---|
| `adk/agent/tenant_user_id.py` | The library itself — validates on every construction or parse. |
| `scripts/memory_isolation_proof.py` | Behavioral proof; runs the contract end-to-end against the live engine (see "Verification" below). |
| Future: `adk/deploy.py` invocation wrappers | When the SDK adds a server-side `runVertexAgent(tenant_id, user_id, …)` surface, the boundary handler calls `require_scoped_user_id(f"{tenant_id}:{user_id}")` before forwarding. (Gateway PR `olympus-cloud-gcp#4957` lands the route; SDK PR `olympus-sdk-dart#144` lands the client.) |

## Verification

The behavioral proof exercises five claims against the deployed agent in `olympuscloud-dev`:

1. **Contract construction**: `scoped_user_id` builds the wire form; round-trip parse returns the original parts.
2. **Tenant A writes a session**: an inventory query streams the full Ceres event trace (root → `transfer_to_agent(levels_agent)` → tool calls → composed report).
3. **Tenant A sees its own session**: `list_sessions(user_id=tenant_a)` includes the new session.
4. **Tenant B does not see tenant A's session**: `list_sessions(user_id=tenant_b)` returns zero items including tenant A's id. This is the **isolation primitive itself**.
5. **Failure injection**: constructing or parsing a user_id without the prefix raises `TenantPrefixError`. The runtime guard rejects the bad call before it ever reaches Vertex.

Run the proof:

```bash
cd olympus-hackathon-2026
python -m venv .venv && source .venv/bin/activate
pip install "google-cloud-aiplatform[agent_engines,adk]"
python scripts/memory_isolation_proof.py
```

Captured output (run 2026-05-24) is checked in at [`demo/memory-isolation-proof.txt`](../../demo/memory-isolation-proof.txt).

## Scope notes

- **Session-list isolation vs. async_search_memory**: the proof asserts session-list isolation (`list_sessions(user_id=B)` does not see tenant A's session). Agent Memory Bank's `async_search_memory` shares the same per-user_id substrate, so the structural guarantee extends — but the proof harness here exercises the session surface only. Adding an `async_search_memory` round-trip is tracked as a follow-up enhancement once the agent flow uses Memory Bank for cross-session recall.
- **Production tenant ids**: same `[A-Za-z0-9_-]+` shape; production tenant ids are UUIDs (which pass the slug regex).
- **The contract is the IP gate**: the contract itself is public-safe and small. The closed monorepo's Ether router + tier catalog + classifier are NOT involved in the isolation primitive — Memory Bank isolation is a substrate property, not a routing decision.

## Survey-answer hook

H10's survey answer #1 ("most critical feature + what's missing") cites this design as evidence that Agent Memory Bank's per-user_id scoping is the right primitive for multi-tenant SaaS — provided the SDK / gateway layer encodes tenant identity into the user_id. The proof script + this doc are the receipts.
