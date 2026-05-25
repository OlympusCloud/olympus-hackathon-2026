"""Unit tests for the tenant-prefixed user_id contract.

These tests do not touch Vertex AI — they exercise the in-process
validation only. Run with: ``pytest adk/test_tenant_user_id.py``.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

# agent/__init__.py is lazy now (resolves root_agent only on attribute
# access) so this clean import doesn't pull google.adk.
from agent.tenant_user_id import (  # noqa: E402
    ScopedUserId,
    TenantPrefixError,
    parse_scoped_user_id,
    require_scoped_user_id,
    scoped_user_id,
)

# Silence unused-import lints for stdlib helpers we no longer need.
_ = importlib
_ = pathlib


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_scoped_user_id_happy_path():
    assert scoped_user_id("demo-tenant-a", "user-1") == "demo-tenant-a:user-1"


def test_scoped_user_id_rejects_empty_tenant():
    with pytest.raises(TenantPrefixError, match="tenant_id is required"):
        scoped_user_id("", "user-1")


def test_scoped_user_id_rejects_empty_user():
    with pytest.raises(TenantPrefixError, match="user_id is required"):
        scoped_user_id("demo-tenant-a", "")


def test_scoped_user_id_rejects_colon_in_tenant():
    with pytest.raises(TenantPrefixError):
        scoped_user_id("demo:tenant", "user-1")


def test_scoped_user_id_rejects_colon_in_user():
    with pytest.raises(TenantPrefixError):
        scoped_user_id("demo-tenant-a", "user:1")


def test_scoped_user_id_rejects_non_slug_characters():
    with pytest.raises(TenantPrefixError):
        scoped_user_id("demo tenant", "user-1")
    with pytest.raises(TenantPrefixError):
        scoped_user_id("demo-tenant-a", "user@1")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parse_scoped_user_id_happy_path():
    parsed = parse_scoped_user_id("demo-tenant-a:user-1")
    assert parsed == ScopedUserId(tenant_id="demo-tenant-a", user_id="user-1")


def test_parse_rejects_missing_prefix():
    with pytest.raises(TenantPrefixError, match="missing"):
        parse_scoped_user_id("user-1")


def test_parse_rejects_empty_string():
    with pytest.raises(TenantPrefixError):
        parse_scoped_user_id("")


def test_parse_rejects_multiple_colons():
    # Greedy split would silently accept "a:b:c" as ("a", "b:c"). We reject
    # to keep the decomposition unambiguous.
    with pytest.raises(TenantPrefixError, match="more than one"):
        parse_scoped_user_id("a:b:c")


def test_parse_rejects_empty_segments():
    # "tenant:" or ":user" each fail the slug regex on the empty side.
    with pytest.raises(TenantPrefixError):
        parse_scoped_user_id("demo-tenant-a:")
    with pytest.raises(TenantPrefixError):
        parse_scoped_user_id(":user-1")


def test_scoped_property_round_trips():
    parsed = parse_scoped_user_id("demo-tenant-b:user-99")
    assert parsed.scoped == "demo-tenant-b:user-99"


# ---------------------------------------------------------------------------
# Runtime guard
# ---------------------------------------------------------------------------


def test_require_scoped_user_id_passes_valid():
    parsed = require_scoped_user_id("demo-tenant-a:user-1")
    assert parsed.tenant_id == "demo-tenant-a"
    assert parsed.user_id == "user-1"


def test_require_scoped_user_id_failure_injection():
    # H6 ac-4: the wrapper must reject any call site that forgot the prefix.
    with pytest.raises(TenantPrefixError):
        require_scoped_user_id("forgot-to-prefix")
