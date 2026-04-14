from __future__ import annotations

from typing import Any


def base_meta_context(**overrides: Any) -> dict[str, Any]:
    context = {
        "meta_title": "Global Payroll Software | Multi-Country Payroll & Compliance Platform | ExactusPay",
        "meta_description": (
            "ExactusPay is a powerful global payroll software delivering multi-country payroll, "
            "automated compliance, real-time workforce analytics, standardized reporting, and payroll simulations."
        ),
        "meta_keywords": (
            "global payroll software, multi-country payroll, international payroll system, "
            "payroll compliance software, global payroll platform, payroll automation"
        ),
        "canonical_path": "/",
    }
    context.update(overrides)
    return context
