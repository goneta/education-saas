"""Payroll calculation engine (#7).

A small, country-extensible engine that turns a set of earnings and deductions
into a full gross → net breakdown. The default strategy applies flat social
contribution and income-tax rates; country-specific rules can be registered with
``@register("SN")`` and override the maths (progressive brackets, ceilings, …)
without touching callers. Pure functions, no I/O, so it is trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class PayslipLine:
    type: str          # allowance | bonus | overtime | deduction | advance
    label: str
    amount: float
    is_taxable: bool = True


@dataclass
class PayslipComputation:
    base_amount: float
    allowances_total: float
    bonus_total: float
    overtime_total: float
    advances_total: float
    other_deductions_total: float
    gross_amount: float
    social_contributions: float
    tax_amount: float
    total_deductions: float
    net_amount: float
    lines: List[PayslipLine] = field(default_factory=list)


EARNINGS = {"allowance", "bonus", "overtime"}
DEDUCTIONS = {"deduction", "advance"}

Strategy = Callable[..., PayslipComputation]
_STRATEGIES: Dict[str, Strategy] = {}


def register(country_code: str) -> Callable[[Strategy], Strategy]:
    def _wrap(fn: Strategy) -> Strategy:
        _STRATEGIES[country_code.upper()] = fn
        return fn
    return _wrap


def _round(value: float) -> float:
    return round(float(value or 0), 2)


def _sum(lines: List[PayslipLine], kind: str) -> float:
    return _round(sum(line.amount for line in lines if line.type == kind))


def default_strategy(
    base_amount: float,
    lines: List[PayslipLine],
    cotisation_rate: float,
    tax_rate: float,
) -> PayslipComputation:
    base_amount = _round(base_amount)
    allowances = _sum(lines, "allowance")
    bonus = _sum(lines, "bonus")
    overtime = _sum(lines, "overtime")
    advances = _sum(lines, "advance")
    other_deductions = _sum(lines, "deduction")

    gross = _round(base_amount + allowances + bonus + overtime)
    cotisations = _round(gross * max(cotisation_rate or 0, 0))
    taxable_base = max(gross - cotisations, 0)
    tax = _round(taxable_base * max(tax_rate or 0, 0))
    total_deductions = _round(cotisations + tax + other_deductions + advances)
    net = _round(gross - total_deductions)

    return PayslipComputation(
        base_amount=base_amount,
        allowances_total=allowances,
        bonus_total=bonus,
        overtime_total=overtime,
        advances_total=advances,
        other_deductions_total=other_deductions,
        gross_amount=gross,
        social_contributions=cotisations,
        tax_amount=tax,
        total_deductions=total_deductions,
        net_amount=net,
        lines=lines,
    )


def compute(
    base_amount: float,
    lines: List[PayslipLine],
    cotisation_rate: float = 0,
    tax_rate: float = 0,
    country_code: Optional[str] = None,
) -> PayslipComputation:
    """Compute a payslip breakdown using the country strategy when registered,
    otherwise the default flat-rate strategy."""
    strategy = _STRATEGIES.get((country_code or "").upper())
    if strategy is not None:
        return strategy(base_amount=base_amount, lines=lines, cotisation_rate=cotisation_rate, tax_rate=tax_rate)
    return default_strategy(base_amount, lines, cotisation_rate, tax_rate)


def base_amount_for(pay_type: str, base_rate: float, units: float) -> float:
    """Resolve the period base pay from the rate and worked units. Hourly/daily/
    weekly multiply the rate by units; monthly is a fixed amount (units ignored)."""
    rate = float(base_rate or 0)
    if pay_type in ("hourly", "daily", "weekly"):
        return _round(rate * float(units or 0))
    return _round(rate)
