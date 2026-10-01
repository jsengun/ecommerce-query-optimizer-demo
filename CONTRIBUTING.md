# Contributing & branching strategy

This project uses a lightweight **GitHub Flow** model: `main` is always
deployable, and all work happens on short-lived branches that merge back through
reviewed pull requests. This keeps parallel work from colliding and keeps the
default branch green.

## Branch model

- **`main`** — the single source of truth. Protected: no direct pushes, every
  change arrives through a pull request that passed CI.
- **`feature/<short-name>`** — a new capability, e.g. `feature/rating-index`.
- **`fix/<short-name>`** — a bug fix, e.g. `fix/checkout-lock-timeout`.

Short-lived branches (hours to a few days) are easier to review and produce far
smaller, cleaner merges than long-running branches that drift from `main`.

## Workflow

1. **Sync and branch off `main`:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/rating-index
   ```
2. **Commit small, focused changes** with clear messages:
   ```bash
   git commit -m "Add composite index on products(category_id, price, rating)"
   ```
3. **Push and open a pull request** against `main`:
   ```bash
   git push -u origin feature/rating-index
   ```
4. **Let CI run.** The [CI workflow](.github/workflows/ci.yml) lints and tests the
   branch automatically. A PR cannot merge until it is green.
5. **Request a review.** At least one teammate approves before merge. Reviews catch
   logic errors, missing tests, and performance regressions early.
6. **Merge and delete the branch.** Squash-merge to keep `main` history readable,
   then delete the feature branch.

## How this avoids merge conflicts and protects quality

- Small, short-lived branches mean each PR touches little, so conflicts are rare and
  easy to resolve.
- Pulling `main` before branching and rebasing before you push keeps branches close
  to the latest code.
- Required CI checks mean no untested or failing code reaches `main`, so the
  default branch stays releasable at all times.
- Required reviews spread knowledge across the team and give performance-sensitive
  changes (like new indexes or query rewrites) a second set of eyes.

## Running checks locally before you push

```bash
pip install -r requirements.txt
ruff check src tests
pytest -q
```

Running the same checks CI runs means fewer surprises after you open the PR.
