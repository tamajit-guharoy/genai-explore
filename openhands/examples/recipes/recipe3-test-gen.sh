# ─── Target: an untested module ───
# src/services/payment.py — 0% test coverage, 500 lines, 12 functions

openhands --headless --override-with-envs \
  -t "Generate a comprehensive test suite for src/services/payment.py.
       Requirements:
       1. Use pytest (the project standard)
       2. Write tests to tests/services/test_payment.py
       3. Cover ALL functions: process_payment, refund, calculate_tax,
          validate_card, create_invoice, etc.
       4. Include edge cases: zero amounts, negative amounts, max values,
          invalid card numbers, expired cards, network failures
       5. Mock external services (Stripe API, tax calculator)
       6. Aim for >90% line coverage
       7. All tests must pass: run pytest tests/services/test_payment.py
          and iterate until green"

# ─── Verify ───
pytest tests/services/test_payment.py --cov=src/services/payment --cov-report=term
# Expected: 90%+ coverage, all tests pass