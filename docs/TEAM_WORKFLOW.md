# Team workflow — read this once

What gets checked at review: **number of commits, whether they're spread across the sprint (not all on one day), number of PRs, tools used, and whether sprint deadlines were met.** Everything below is set up for exactly that.

We don't use Jira (mentor approved). Stories are **GitHub Issues**, the board is a **GitHub Projects** board, sprints are **milestones** ("Sprint 1", "Sprint 2").

## One-time setup (each person)

1. Accept the GitHub collaborator invite (the repo lives on Sathya's account, `TSSathyaKiran`).
2. Clone and set your identity — **use the email linked to your GitHub account**, otherwise your commits won't count as yours:
   ```bash
   git clone https://github.com/TSSathyaKiran/SE_MINIPROJECT.git
   cd SE_MINIPROJECT
   git config user.name "Your Name"
   git config user.email "your-github-email@example.com"
   ```
3. Install Python 3.11 and create a virtualenv: `python3.11 -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
4. Windows: run the `bash scripts/...` commands from **Git Bash**, not PowerShell.

## One-time setup: GitHub (Sathya, repo owner)

- Push the first commit to `main`, then invite Tanuj, Vaishnavi and Srujan under Settings → Collaborators.
- Create the issues **before anyone opens a PR**, so issue #n = backlog row #n: `brew install gh && gh auth login`, then `bash scripts/create_issues.sh`. Assign each issue to its owner.
- Projects tab → New project → **Board**. Add all issues. In the project's Workflows, turn on "Auto-add to project" for this repo, and "Item closed" / "Pull request merged" → Done. Give Tanuj admin access to the project.
- Settings → Branches → add a rule for `main`: require a pull request and 1 approval. After CI has run once on a PR, also tick "require status checks" → `test`. Now nobody (including the owner) can push straight to main. (On a private repo this needs GitHub Pro, which is free with the GitHub Student Pack; otherwise make the repo public.)
- Settings → General → Pull Requests: leave only "Allow merge commits" ticked. Squash merging would collapse each PR into one commit on main and hide everyone's individual commits.

## One-time setup: sprints (Tanuj, Scrum Master)

- Issues → Milestones: set the due dates on "Sprint 1" and "Sprint 2" to the real deadlines.

## Every story (the loop)

`scripts/g.sh` handles the branch name, the issue number and the message format for you:

```bash
bash scripts/g.sh start 8 student-create            # fresh main -> branch feature/8-student-create
#   ...build one small step, make sure the tests pass, then:
bash scripts/g.sh commit feat students "add POST /students with validation"
#   -> runs pytest, shows the files, asks y/N, commits "feat(students): add POST /students with validation (#8)"
#   ...repeat for each step...
bash scripts/g.sh push                              # pushes and prints the "open PR" link
```

If main moved while you worked: `bash scripts/g.sh sync`.

Then open the link it printed (base `main`), paste the PR text (it starts with `Closes #8`), and request a review from a teammate. Move the card to **In Review**. After it's approved and CI is green, Tanuj (or the author) merges it; the issue closes itself and the card goes to **Done**.

## Making commits look (and be) real

- **Commit every time something small works** — a route, a validation rule, a test. 3–8 commits per story is normal.
- **Work a bit every day of the sprint.** Even 30–60 minutes a day with 2–3 commits is way better than 15 commits on the last night. The graph shows dates.
- **Don't fake dates** (`--date`, `GIT_COMMITTER_DATE`, rebasing old commits). It's easy to spot, and the PR timestamps on GitHub can't be changed anyway.
- Write messages that say what changed: `fix(enrollment): reject duplicate enrollment with 409 (#13)` — not `update`, `changes`, `final`, `asdf`.
- Separate commits for code and its tests is fine and adds clarity.
- Docs, test scripts, seed data, JMeter plans, CI fixes — all real commits. Testers (Sathya, Vaishnavi) should be committing test code regularly, not only features.

## Board habits

- Move your card when you start (In Progress) and when you open the PR (In Review). Merging moves it to Done. Do it the same day.
- When a test fails, open a GitHub Issue with the `bug` label, then fix it on `fix/<bug-issue-number>-name` with `Closes #<n>` in the PR.
- Tanuj: at the end of each sprint, screenshot the board, the milestone page (% complete) and the project's Insights chart for the review.

## Daily 5-minute check (on WhatsApp is fine)

Each person: what I merged / what I'm on / am I blocked. Tanuj updates the board.

## Before each sprint deadline

- [ ] All sprint issues are closed, or moved to the next milestone with a comment saying why
- [ ] `main` runs: `python src/run.py` and login works for every role
- [ ] `pytest -q` green on main
- [ ] RTM.csv status column updated (N → P → A/F)
- [ ] Demo video recorded and committed (Sprint 1: 1 min, Sprint 2: 2 min)
- [ ] Any change from the SRS/SAD/Test Plan written in `docs/DEVIATIONS.md`
