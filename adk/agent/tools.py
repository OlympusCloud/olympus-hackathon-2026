"""Ceres tool functions — public-safe stubs that return realistic demo data.

In production these tools call into the Olympus API gateway (private
monorepo). For the hackathon carve-out they return canned data so the
agent's workflow can be demonstrated end-to-end without exposing the
real backend or requiring a customer's data plane to be reachable.

Names + signatures + return shapes mirror the corresponding handlers in
the private monorepo so the ADK agent's tool surface is a faithful 1:1
to the LangGraph node-side implementations.
"""

from __future__ import annotations

from datetime import date, timedelta


def load_inventory(
    tenant_id: str,
    location_filter: list[str] | None = None,
    category_filter: list[str] | None = None,
) -> dict:
    """Fetch the current inventory snapshot for a tenant.

    In production: reads from the Olympus inventory service. Here:
    returns a 4-item canned set covering the threshold-classification
    edge cases (one critical, one low, one normal, one overstocked).
    """
    return {
        "inventory_items": [
            {"sku": "BUR-001", "name": "Beef Burger Patty 6oz", "current_qty": 8,  "par_level": 80,  "reorder_point": 20, "unit_cost": 2.10, "category": "protein"},
            {"sku": "BUN-002", "name": "Brioche Bun",           "current_qty": 40, "par_level": 120, "reorder_point": 30, "unit_cost": 0.45, "category": "bread"},
            {"sku": "FRY-003", "name": "Frozen Fries 5lb",      "current_qty": 60, "par_level": 80,  "reorder_point": 20, "unit_cost": 6.75, "category": "produce"},
            {"sku": "LET-004", "name": "Romaine Lettuce",       "current_qty": 90, "par_level": 30,  "reorder_point": 10, "unit_cost": 1.20, "category": "produce"},
        ],
        "inventory_summary": {
            "total_skus": 4,
            "total_value_at_cost": 8 * 2.10 + 40 * 0.45 + 60 * 6.75 + 90 * 1.20,
            "tenant_id": tenant_id,
            "filters_applied": {
                "locations": location_filter or [],
                "categories": category_filter or [],
            },
        },
    }


def evaluate_stock_levels(inventory_items: list[dict]) -> dict:
    """Classify each item as critical / low / normal / overstocked.

    Thresholds match the source: <=0 out_of_stock; <0.25 critical;
    <0.50 low; >1.50 overstocked; otherwise normal.
    """
    critical, low, overstocked = 0.25, 0.50, 1.50
    alerts = []
    for item in inventory_items:
        ratio = item["current_qty"] / max(item["par_level"], 1)
        if item["current_qty"] <= 0:
            status = "out_of_stock"
        elif ratio < critical:
            status = "critical"
        elif ratio < low:
            status = "low"
        elif ratio > overstocked:
            status = "overstocked"
        else:
            status = "normal"
        if status in ("out_of_stock", "critical", "low", "overstocked"):
            alerts.append({
                "sku": item["sku"], "name": item["name"],
                "current_qty": item["current_qty"], "par_level": item["par_level"],
                "status": status, "ratio": round(ratio, 2),
            })
    return {"stock_alerts": alerts}


def compute_reorder_suggestions(inventory_items: list[dict]) -> dict:
    """Suggest reorder quantities for items at or below reorder point."""
    suggestions = []
    for item in inventory_items:
        if item["current_qty"] <= item["reorder_point"]:
            qty = max(item["par_level"] - item["current_qty"], 0)
            suggestions.append({
                "sku": item["sku"], "name": item["name"],
                "reorder_qty": qty,
                "estimated_cost": round(qty * item["unit_cost"], 2),
            })
    return {"reorder_suggestions": suggestions}


def forecast_demand(inventory_items: list[dict], horizon_days: int = 14) -> dict:
    """Per-SKU demand forecast for the next horizon (default 14 days)."""
    today = date.today()
    forecasts = []
    for item in inventory_items:
        # Canned: expected daily demand ≈ par_level / 7 (one week's stock = par)
        daily = item["par_level"] / 7
        forecasts.append({
            "sku": item["sku"], "name": item["name"],
            "horizon_days": horizon_days,
            "expected_total_demand": round(daily * horizon_days),
            "lower_bound": round(daily * horizon_days * 0.75),
            "upper_bound": round(daily * horizon_days * 1.25),
            "confidence": 0.78,
            "forecast_through": (today + timedelta(days=horizon_days)).isoformat(),
        })
    return {"demand_forecasts": forecasts}


def load_waste_data(tenant_id: str, location_filter: list[str] | None = None) -> dict:
    """Last-30-day shrink / waste / expiry events for a tenant."""
    return {
        "waste_data": [
            {"sku": "LET-004", "date": (date.today() - timedelta(days=2)).isoformat(), "qty": 6,  "reason": "expiry"},
            {"sku": "BUR-001", "date": (date.today() - timedelta(days=5)).isoformat(), "qty": 2,  "reason": "spoilage"},
        ],
        "waste_analysis": {
            "total_waste_cost_30d": 6 * 1.20 + 2 * 2.10,
            "waste_rate_30d": 0.038,  # 3.8 % — under the 5 % alert threshold
            "top_waste_sku": "LET-004",
            "tenant_id": tenant_id,
        },
    }


def load_supplier_data(tenant_id: str) -> dict:
    """Supplier scorecard + per-supplier reliability score."""
    return {
        "supplier_data": [
            {"supplier_id": "sup-1", "name": "Meridian Foods",   "on_time": 0.94, "fill_rate": 0.97, "defect_rate": 0.01, "reliability": 0.92},
            {"supplier_id": "sup-2", "name": "Harvest Direct",   "on_time": 0.71, "fill_rate": 0.83, "defect_rate": 0.05, "reliability": 0.66},
            {"supplier_id": "sup-3", "name": "Coastal Produce",  "on_time": 0.88, "fill_rate": 0.93, "defect_rate": 0.02, "reliability": 0.87},
        ],
        "supplier_analysis": {
            "below_threshold": ["sup-2"],  # 0.80 reliability gate
            "average_reliability": 0.82,
            "tenant_id": tenant_id,
        },
    }


def compute_inventory_valuation(inventory_items: list[dict]) -> dict:
    """Total inventory valuation at cost, broken down by category."""
    by_category: dict[str, float] = {}
    total = 0.0
    for item in inventory_items:
        value = item["current_qty"] * item["unit_cost"]
        total += value
        by_category[item["category"]] = round(
            by_category.get(item["category"], 0) + value, 2
        )
    return {
        "valuation": {
            "total_at_cost": round(total, 2),
            "by_category": by_category,
        },
    }


def dispatch_alerts(tenant_id: str, alerts: list[str]) -> dict:
    """Send the alert list to the tenant's notification surfaces.

    Public stub: no-op + structured ack. The real handler routes to
    in-app + email + SMS + Slack + Teams + voice per tenant config.
    """
    return {
        "dispatched": len(alerts),
        "tenant_id": tenant_id,
        "channels_used": ["demo-stub"],
    }
