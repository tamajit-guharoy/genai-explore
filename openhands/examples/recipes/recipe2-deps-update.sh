# ─── Step 1: Update all dependencies ───
pip install --upgrade -r requirements.txt

# ─── Step 2: Run tests to see what broke ───
pytest 2>&1 | tee test-output.txt

# ─── Step 3: Have OpenHands fix the breakage ───
# Pass the test output so the agent knows exactly what failed
openhands --headless --override-with-envs \
  -t "Dependencies were just updated. Tests are failing.
       The test output is in test-output.txt.
       Fix all test failures by updating code to work with new dependency versions.
       Do NOT downgrade any packages — fix the code, not the versions."

# ─── Step 4: Verify everything passes ───
pytest && echo "✓ All tests pass with updated dependencies"

# ─── Step 5: Commit ───
git add -A
git commit -m "chore: update dependencies and fix compatibility"