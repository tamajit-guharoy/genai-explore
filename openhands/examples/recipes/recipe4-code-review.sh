# ─── Get the PR diff ───
gh pr diff 123 > pr_diff.txt

# ─── Have OpenHands review it ───
openhands --headless --override-with-envs \
  -t "Review the PR diff in pr_diff.txt.
       Write your review to REVIEW.md with these sections:
       1. Summary: what this PR does
       2. Bugs Found: actual logic errors (NOT style nits)
       3. Security Issues: injection risks, exposed secrets, auth bypasses
       4. Performance: N+1 queries, unnecessary allocations, blocking calls
       5. Test Quality: missing edge cases, brittle assertions
       6. Recommendation: APPROVE, REQUEST_CHANGES, or COMMENT

       Only flag REAL issues — not personal preferences.
       Cite specific line numbers from the diff."

# ─── Post the review to GitHub ───
gh pr review 123 --body "$(cat REVIEW.md)"