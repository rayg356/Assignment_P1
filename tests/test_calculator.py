import math

import pytest

from loan_calc.calculator import (
    InvalidInstalmentError,
    InvalidPrepaymentError,
    InvalidPrincipalError,
    InvalidRateError,
    InvalidTenureError,
    ValidationError,
    amortisation_schedule,
    compare_offers,
    eligible_amount,
    emi,
    format_inr,
    outstanding_after,
    prepayment_savings,
    remaining_tenure,
    schedule_to_csv,
    summary,
    total_interest,
    total_payment,
)


def test_emi_known_value():
    # Acceptance criterion: ₹10,00,000 at 9% for 240 months ~= ₹8,997 (±1)
    value = emi(1_000_000, 9, 240)
    assert 8996 <= value <= 8998


def test_emi_zero_interest():
    assert emi(120_000, 0, 12) == 10000.00


def test_emi_one_month_tenure():
    # One-month tenure should return principal + one month interest
    assert emi(100_000, 12, 1) == 101000.00


def test_emi_invalid_inputs():
    with pytest.raises(InvalidPrincipalError):
        emi(0, 9, 240)
    with pytest.raises(InvalidTenureError):
        emi(100_000, 9, 0)
    with pytest.raises(InvalidRateError):
        emi(100_000, -1, 240)


def test_total_payment_and_interest():
    principal = 500_000
    rate = 8.5
    tenure = 120
    tp = total_payment(principal, rate, tenure)
    ti = total_interest(principal, rate, tenure)
    assert tp > principal
    assert ti == round(tp - principal, 2)


def test_amortisation_schedule_length_and_last_balance_zeroish():
    rows = amortisation_schedule(500_000, 9, 60)
    assert len(rows) == 60
    assert rows[-1]["month"] == 60
    assert rows[-1]["balance"] == 0.0


def test_outstanding_after_behavior():
    principal = 300_000
    rate = 10
    tenure = 36
    assert outstanding_after(principal, rate, tenure, 0) == round(principal, 2)
    assert outstanding_after(principal, rate, tenure, 999) == 0.0
    mid = outstanding_after(principal, rate, tenure, 12)
    assert 0 < mid < principal


def test_remaining_tenure_zero_rate():
    assert remaining_tenure(100_000, 0, 10_000) == 10


def test_remaining_tenure_instalment_too_small():
    with pytest.raises(InvalidInstalmentError):
        remaining_tenure(100_000, 12, 100)


def test_remaining_tenure_invalid_instalment_zero():
    with pytest.raises(InvalidInstalmentError):
        remaining_tenure(100_000, 9, 0)


def test_prepayment_savings_reduces_tenure_and_saves_interest():
    out = prepayment_savings(1_000_000, 9, 240, prepay_month=24, prepay_amount=100_000)
    assert out["months_saved"] > 0
    assert out["new_tenure"] < 240
    assert out["interest_saved"] > 0


def test_prepayment_larger_than_balance():
    # Large prepayment should close loan immediately after prepay month
    out = prepayment_savings(200_000, 9, 24, prepay_month=20, prepay_amount=1_000_000)
    assert out["new_tenure"] == 20
    assert out["months_saved"] == 4


def test_prepayment_invalid_inputs():
    with pytest.raises(InvalidPrepaymentError):
        prepayment_savings(200_000, 9, 24, prepay_month=0, prepay_amount=1_000)
    with pytest.raises(InvalidPrepaymentError):
        prepayment_savings(200_000, 9, 24, prepay_month=25, prepay_amount=1_000)
    with pytest.raises(InvalidPrepaymentError):
        prepayment_savings(200_000, 9, 24, prepay_month=5, prepay_amount=-1)


def test_compare_offers_sorted_by_total_cost():
    offers = [
        {"bank": "A", "rate": 9.2, "tenure": 240, "processing_fee_pct": 0.2},
        {"bank": "B", "rate": 9.0, "tenure": 240, "processing_fee_pct": 0.5},
        {"bank": "C", "rate": 8.9, "tenure": 240},
    ]
    result = compare_offers(1_000_000, offers)
    costs = [x["total_cost"] for x in result]
    assert costs == sorted(costs)


def test_compare_offers_validation_errors():
    with pytest.raises(ValidationError):
        compare_offers(1_000_000, [])
    with pytest.raises(ValidationError):
        compare_offers(1_000_000, [{"bank": "A", "rate": 9.1}])


def test_eligible_amount_zero_interest():
    # available = 100000 * 0.5 - 10000 = 40000; amount = 40000 * 12
    assert eligible_amount(100_000, 10_000, 0, 12) == 480000.00


def test_eligible_amount_no_capacity():
    assert eligible_amount(20_000, 15_000, 10, 120, foir=0.5) == 0.0


def test_eligible_amount_validation_errors():
    with pytest.raises(ValidationError):
        eligible_amount(0, 10_000, 9, 120)
    with pytest.raises(ValidationError):
        eligible_amount(100_000, -1, 9, 120)
    with pytest.raises(ValidationError):
        eligible_amount(100_000, 10_000, -1, 120)
    with pytest.raises(ValidationError):
        eligible_amount(100_000, 10_000, 9, 0)
    with pytest.raises(ValidationError):
        eligible_amount(100_000, 10_000, 9, 120, foir=0)


def test_format_inr():
    assert format_inr(1234567.89) == "₹12,34,567.89"
    assert format_inr(-1000) == "-₹1,000.00"


def test_format_inr_validation_error():
    with pytest.raises(ValidationError):
        format_inr("not-a-number")


def test_schedule_to_csv(tmp_path):
    rows = amortisation_schedule(100_000, 10, 3)
    out_file = tmp_path / "schedule.csv"
    schedule_to_csv(rows, str(out_file))
    text = out_file.read_text()
    assert text.startswith("month,emi,interest,principal,balance\n")
    assert "1," in text


def test_schedule_to_csv_validation_errors(tmp_path):
    with pytest.raises(ValidationError):
        schedule_to_csv([], str(tmp_path / "x.csv"))
    with pytest.raises(ValidationError):
        schedule_to_csv([{"month": 1, "emi": 1.0, "interest": 0.0, "principal": 1.0, "balance": 0.0}], "")


def test_summary_structure():
    s = summary(1_000_000, 9, 240)
    assert s["currency"] == "INR"
    assert s["principal"].startswith("₹")
    assert s["emi"].startswith("₹")
    assert s["tenure"] == "240 months"


def test_very_large_principal_no_overflow():
    # Very large principal edge case
    huge = 10_000_000_000  # 10 billion
    e = emi(huge, 8.5, 360)
    assert math.isfinite(e)
    assert e > 0
