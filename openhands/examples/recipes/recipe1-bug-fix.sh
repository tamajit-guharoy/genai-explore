# ─── Step 1: Clone and set up ───
git clone https://github.com/your-org/your-repo.git
cd your-repo
git checkout -b fix/issue-42

# ─── Step 2: Run OpenHands with the issue ───
# The agent reads the codebase, identifies the bug, writes a fix + tests
openhands --headless --override-with-envs \
  -t "Fix issue #42: DatePicker crashes when selecting Feb 29 in non-leap years.
       The bug report says the crash is in src/components/DatePicker.tsx line 142.
       Write a fix, add a unit test for the leap-year edge case,
       and verify all existing tests still pass."

# ─── Step 3: Review the agent's work ───
git diff
npm test

# ─── Step 4: Commit and create PR ───
git add -A
git commit -m "fix: DatePicker crash on Feb 29 in non-leap years

Adds leap-year validation before creating Date object.
Includes unit test for edge case.
Closes #42"
git push origin fix/issue-42
gh pr create --title "Fix: DatePicker Feb 29 crash (#42)" \
    --body "Automated fix by OpenHands. Adds validation + test."