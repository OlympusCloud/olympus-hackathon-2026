"""Tenant-prefixed user_id contract for Agent Memory Bank isolation.

Agent Memory Bank persists per-`user_id` across sessions. To ensure
tenant A's agent runs cannot read tenant B's memory we encode
`tenant_id` as the first segment of every `user_id` passed to
Vertex AI Agent Engine.

Format: ``"{tenant_id}:{user_id}"`` (e.g. ``"demo-tenant-a:hackathon-user-1"``).

The :func:`scoped_user_id` builder is the only call site that should
create user_ids for ``create_session`` / ``stream_query``;
:func:`parse_scoped_user_id` decomposes one back to its parts; and
:func:`require_scoped_user_id` is the runtime guard that rejects any
call site that forgot the prefix.

See ``docs/architecture/agent-memory-bank.md`` for the contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Tenant ids and user ids must each be ASCII slugs (letters, digits, dash,
# underscore). The colon is reserved as the segment separator and must not
# appear inside either component.
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_PREFIX_SEPARATOR = ":"


class TenantPrefixError(ValueError):
    """Raised when a user_id violates the tenant-prefix contract."""


@dataclass(frozen=True)
class ScopedUserId:
    """Parsed tenant-prefixed user_id."""

    tenant_id: str
    user_id: str

    @property
    def scoped(self) -> str:
        return f"{self.tenant_id}{_PREFIX_SEPARATOR}{self.user_id}"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.scoped


def scoped_user_id(tenant_id: str, user_id: str) -> str:
    """Build a tenant-prefixed user_id for a session/query.

    Raises:
        TenantPrefixError: if either segment is empty or contains the
            separator character or a non-slug character.
    """
    if not tenant_id:
        raise TenantPrefixError("tenant_id is required")
    if not user_id:
        raise TenantPrefixError("user_id is required")
    if not _SEGMENT_RE.match(tenant_id):
        raise TenantPrefixError(
            f"tenant_id {tenant_id!r} must match {_SEGMENT_RE.pattern}"
        )
    if not _SEGMENT_RE.match(user_id):
        raise TenantPrefixError(
            f"user_id {user_id!r} must match {_SEGMENT_RE.pattern}"
        )
    return f"{tenant_id}{_PREFIX_SEPARATOR}{user_id}"


def parse_scoped_user_id(raw: str) -> ScopedUserId:
    """Split a scoped user_id back into ``ScopedUserId(tenant_id, user_id)``.

    Raises:
        TenantPrefixError: if the input lacks the ``tenant:user`` shape or
            either segment fails validation.
    """
    if not raw or _PREFIX_SEPARATOR not in raw:
        raise TenantPrefixError(
            f"user_id {raw!r} is missing the {_PREFIX_SEPARATOR!r} tenant prefix"
        )
    head, sep, tail = raw.partition(_PREFIX_SEPARATOR)
    # A second colon is a contract violation — we deliberately reject
    # rather than greedy-split, to avoid ambiguous decomposition.
    if _PREFIX_SEPARATOR in tail:
        raise TenantPrefixError(
            f"user_id {raw!r} contains more than one {_PREFIX_SEPARATOR!r}; "
            "tenant_id and user_id must each be slugs"
        )
    if not _SEGMENT_RE.match(head) or not _SEGMENT_RE.match(tail):
        raise TenantPrefixError(
            f"user_id {raw!r} segments must match {_SEGMENT_RE.pattern}"
        )
    return ScopedUserId(tenant_id=head, user_id=tail)


def require_scoped_user_id(raw: str) -> ScopedUserId:
    """Runtime guard for SDK / handler call sites.

    Wrap every Vertex AI Agent Engine ``user_id`` parameter at the boundary
    layer. Returns the parsed tuple on success; raises
    :class:`TenantPrefixError` on any contract violation so callers fail
    fast at the call site, not deep inside Memory Bank.
    """
    return parse_scoped_user_id(raw)
