# PROMPT_LOG.md

## Prompt history summary (this chat)

### User requests captured in this session
- Asked to find the **3 seeded bugs/fixes first** and show them.
- Asked to **generate docstrings and type hints for every public function**.
- Asked to **propose and write pytest test cases**, explicitly including edge cases:
  - 0% interest
  - 1-month tenure
  - very large principal
  - prepayment larger than balance
- Asked to **run tests**, diagnose failures, and **fix code** (not tests unless test is wrong).
- Asked to **reach at least 85% coverage**.
- Asked to add a **prompt log record** with factual mistakes from this chat.

---

## Record A — Bug-finding response needed correction

### What happened
In the initial bug analysis response, AI explanation was not as crisp as needed for the seeded-fix task, and required tightening to concrete implementation-level fixes.

### Why this matters
Your request was to identify seeded bugs directly and show exact fixes; overly broad explanation was less useful than explicit patch-level statements.

### Corrected outcome
Applied and verified concrete fixes in `calculator.py`:
1. `_monthly_rate` returns direct monthly rate.
2. `amortisation_schedule` iterates through the final month (`range(... + 1)`).
3. `remaining_tenure` uses monthly rate helper.

---

## Record B — Wrong command syntax for your shell

### What happened
AI first ran:

```powershell
cd Assignment_P1-main && python -m pytest -q --cov=. --cov-report=term-missing test_calculator.py
```

### Problem
In your PowerShell session this failed with:
- `The token '&&' is not a valid statement separator in this version.`

### Correction
Changed to PowerShell-compatible chaining:

```powershell
cd Assignment_P1-main; python -m pytest -q --cov=. --cov-report=term-missing test_calculator.py
```

---

## Execution/results log for your testing request

### Test creation task completed
`test_calculator.py` was created with coverage across:
- EMI, total payment, total interest
- amortisation schedule and outstanding balance
- remaining tenure
- prepayment savings
- offer comparison
- eligibility amount
- INR formatting
- CSV schedule export
- summary output

### Edge-case coverage explicitly included
- 0% interest 
- 1-month tenure 
- very large principal 
- prepayment larger than balance 

### Coverage target request completed
Final run result from your terminal:
- 18 passed
- 89% total coverage
- Meets >=85% requirement.

### EMI acceptance check included
Test includes:
- ₹10,00,000 at 9% p.a. over 240 months ≈ ₹8,997 (±1), and it passed.
