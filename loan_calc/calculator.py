import math
from datetime import date


class LoanCalcError(Exception):
    """Base exception for loan calculator errors."""


class ValidationError(LoanCalcError):
    """Raised when input validation fails."""


class InvalidPrincipalError(ValidationError):
    """Raised when principal/balance is invalid."""


class InvalidRateError(ValidationError):
    """Raised when annual interest rate is invalid."""


class InvalidTenureError(ValidationError):
    """Raised when tenure is invalid."""


class InvalidInstalmentError(ValidationError):
    """Raised when instalment amount is invalid."""


class InvalidPrepaymentError(ValidationError):
    """Raised when prepayment input is invalid."""


DEFAULT_CURRENCY = "INR"


def _validate_principal(principal: float) -> None:
    if principal <= 0:
        raise InvalidPrincipalError("principal must be positive")


def _validate_rate(annual_rate: float) -> None:
    if annual_rate < 0:
        raise InvalidRateError("annual_rate cannot be negative")


def _validate_tenure(tenure_months: int) -> None:
    if tenure_months <= 0:
        raise InvalidTenureError("tenure must be positive")


def _validate_instalment(instalment: float) -> None:
    if instalment <= 0:
        raise InvalidInstalmentError("instalment must be positive")


def _monthly_rate(annual_rate):
    _validate_rate(annual_rate)
    return annual_rate / 1200


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate the fixed monthly EMI for a reducing-balance loan."""
    _validate_tenure(tenure_months)
    _validate_principal(principal)
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(principal / tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(principal * r * f / (f - 1), 2)


def total_payment(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Return total amount repaid over the full tenure."""
    return round(emi(principal, annual_rate, tenure_months) * tenure_months, 2)


def total_interest(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Return total interest paid over the full tenure."""
    return round(total_payment(principal, annual_rate, tenure_months) - principal, 2)


def amortisation_schedule(principal: float, annual_rate: float, tenure_months: int) -> list[dict[str, float]]:
    """Build month-by-month amortisation schedule with EMI split and balance."""
    r = _monthly_rate(annual_rate)
    instalment = emi(principal, annual_rate, tenure_months)
    balance = principal
    rows = []
    for month in range(1, tenure_months + 1):
        interest = round(balance * r, 2)
        principal_part = round(instalment - interest, 2)
        if month == tenure_months:
            principal_part = round(balance, 2)
            instalment_amt = round(principal_part + interest, 2)
        else:
            instalment_amt = instalment
        balance = round(balance - principal_part, 2)
        rows.append({
            "month": month,
            "emi": instalment_amt,
            "interest": interest,
            "principal": principal_part,
            "balance": max(balance, 0.0),
        })
    return rows


def outstanding_after(principal: float, annual_rate: float, tenure_months: int, months_paid: int) -> float:
    """Get outstanding balance after a given number of EMIs are paid."""
    if months_paid <= 0:
        return round(principal, 2)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    if months_paid > len(sched):
        return 0.0
    return sched[months_paid - 1]["balance"]


def remaining_tenure(balance: float, annual_rate: float, instalment: float) -> int:
    """Estimate remaining tenure (in months) for a balance and fixed instalment."""
    _validate_instalment(instalment)
    r = _monthly_rate(annual_rate)
    if balance <= 0:
        return 0
    if r == 0:
        return math.ceil(balance / instalment)
    if instalment <= balance * r:
        raise InvalidInstalmentError("instalment too small to repay the loan")
    n = -math.log(1 - balance * r / instalment) / math.log(1 + r)
    return math.ceil(n)


def prepayment_savings(
    principal: float, annual_rate: float, tenure_months: int, prepay_month: int, prepay_amount: float
) -> dict[str, float]:
    """Keep the same EMI after a lump-sum prepayment and shorten the tenure."""
    _validate_principal(principal)
    _validate_rate(annual_rate)
    _validate_tenure(tenure_months)
    if prepay_month <= 0 or prepay_month > tenure_months:
        raise InvalidPrepaymentError("prepay_month must be between 1 and tenure_months")
    if prepay_amount < 0:
        raise InvalidPrepaymentError("prepay_amount cannot be negative")

    instalment = emi(principal, annual_rate, tenure_months)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    balance = sched[prepay_month - 1]["balance"]
    new_balance = balance - prepay_amount
    if new_balance <= 0:
        months_left = 0
    else:
        months_left = remaining_tenure(new_balance, annual_rate, instalment)
    original_left = tenure_months - prepay_month
    interest_paid_so_far = sum(row["interest"] for row in sched[:prepay_month])
    original_interest = total_interest(principal, annual_rate, tenure_months)
    new_total = instalment * prepay_month + prepay_amount + instalment * months_left
    new_interest = new_total - principal
    return {
        "emi": instalment,
        "months_saved": original_left - months_left,
        "new_tenure": prepay_month + months_left,
        "interest_saved": round(original_interest - new_interest, 2),
        "interest_paid_before_prepayment": round(interest_paid_so_far, 2),
    }


def compare_offers(principal: float, offers: list[dict]) -> list[dict]:
    """Compare loan offers and return them sorted by total cost."""
    _validate_principal(principal)
    if not offers:
        raise ValidationError("offers cannot be empty")

    out = []
    for o in offers:
        if "bank" not in o or "rate" not in o or "tenure" not in o:
            raise ValidationError("each offer must contain bank, rate, and tenure")
        e = emi(principal, o["rate"], o["tenure"])
        ti = total_interest(principal, o["rate"], o["tenure"])
        fee = o.get("processing_fee_pct", 0) * principal / 100
        out.append({
            "bank": o["bank"],
            "emi": e,
            "total_interest": ti,
            "processing_fee": round(fee, 2),
            "total_cost": round(ti + fee, 2),
        })
    out.sort(key=lambda x: x["total_cost"])
    return out


def eligible_amount(
    monthly_income: float, existing_emis: float, annual_rate: float, tenure_months: int, foir: float = 0.5
) -> float:
    """Estimate eligible principal amount from income, obligations, and FOIR."""
    if monthly_income <= 0:
        raise ValidationError("monthly_income must be positive")
    if existing_emis < 0:
        raise ValidationError("existing_emis cannot be negative")
    _validate_rate(annual_rate)
    _validate_tenure(tenure_months)
    if not (0 < foir <= 1):
        raise ValidationError("foir must be in the range (0, 1]")

    available = monthly_income * foir - existing_emis
    if available <= 0:
        return 0.0
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(available * tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(available * (f - 1) / (r * f), 2)


def format_inr(amount: float) -> str:
    """Format a number as INR using Indian-style comma grouping."""
    if not isinstance(amount, (int, float)):
        raise ValidationError("amount must be a number")

    neg = amount < 0
    amount = abs(round(amount, 2))
    whole, frac = f"{amount:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "₹" + whole + "." + frac


def schedule_to_csv(rows: list[dict[str, float]], path: str) -> None:
    """Write an amortisation schedule to a CSV file."""
    if not rows:
        raise ValidationError("rows cannot be empty")
    if not path:
        raise ValidationError("path cannot be empty")

    with open(path, "w") as fh:
        fh.write("month,emi,interest,principal,balance\n")
        for r in rows:
            fh.write(f'{r["month"]},{r["emi"]},{r["interest"]},{r["principal"]},{r["balance"]}\n')


def summary(principal: float, annual_rate: float, tenure_months: int, start: date | None = None) -> dict[str, str]:
    """Return a user-friendly summary of the loan with formatted values."""
    start = start or date.today()
    e = emi(principal, annual_rate, tenure_months)
    end_year = start.year + (start.month - 1 + tenure_months) // 12
    end_month = (start.month - 1 + tenure_months) % 12 + 1
    return {
        "principal": format_inr(principal),
        "rate": f"{annual_rate}% p.a.",
        "tenure": f"{tenure_months} months",
        "emi": format_inr(e),
        "total_interest": format_inr(total_interest(principal, annual_rate, tenure_months)),
        "total_payment": format_inr(total_payment(principal, annual_rate, tenure_months)),
        "last_emi": f"{end_year}-{end_month:02d}",
        "currency": DEFAULT_CURRENCY,
    }
