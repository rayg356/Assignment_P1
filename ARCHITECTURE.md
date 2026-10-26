# loan-calc Architecture Notes

This document explains what each part of the assignment does, based on the current codebase.

## Project Structure

- `loan_calc/calculator.py` - Core loan calculations and helper functions.
- `loan_calc/__init__.py` - Exposes public functions from `calculator.py`.
- `cli.py` - Command-line interface for running calculations.
- `README.md` - Setup and usage guide.
- `tests/` - Unit tests for loan calculations.

---

## Constants

- `DEFAULT_CURRENCY`
  - Default currency used in loan summaries (`INR`).

---

## Helper Functions

- `_monthly_rate(annual_rate)`
  - Converts an annual interest rate into a monthly decimal rate.

---

## Loan Calculations

- `emi(principal, annual_rate, tenure_months)`
  - Calculates the monthly loan instalment using the standard EMI formula.

- `total_payment(principal, annual_rate, tenure_months)`
  - Calculates the total amount repaid over the loan term.

- `total_interest(principal, annual_rate, tenure_months)`
  - Calculates total interest paid throughout the loan.

---

## Amortisation and Balances

- `amortisation_schedule(principal, annual_rate, tenure_months)`
  - Generates a month-by-month repayment schedule showing EMI, interest, principal repaid and remaining balance.

- `outstanding_after(principal, annual_rate, tenure_months, months_paid)`
  - Returns the remaining loan balance after a specified number of payments.

---

## Prepayment Features

- `remaining_tenure(balance, annual_rate, instalment)`
  - Estimates how many months are required to clear a remaining balance.

- `prepayment_savings(...)`
  - Calculates the impact of a lump-sum prepayment, including tenure and interest savings.

---

## Offer Comparison and Eligibility

- `compare_offers(principal, offers)`
  - Compares loan offers based on interest, fees and overall borrowing cost.

- `eligible_amount(monthly_income, existing_emis, annual_rate, tenure_months, foir=0.5)`
  - Estimates the maximum loan amount a borrower can afford.

---

## Formatting and Export

- `format_inr(amount)`
  - Formats values using Indian currency notation.

- `schedule_to_csv(rows, path)`
  - Exports an amortisation schedule to a CSV file.

---

## Summary

- `summary(principal, annual_rate, tenure_months, start=None)`
  - Produces a formatted loan summary including EMI, total repayment, interest and loan completion date.

---

## CLI

The command-line interface accepts loan details as input and can:

- Display loan summaries
- Print amortisation schedules
- Calculate prepayment savings

---

## Package Exports

### `loan_calc/__init__.py`

Re-exports calculator functions so callers can import directly from the `loan_calc` package.