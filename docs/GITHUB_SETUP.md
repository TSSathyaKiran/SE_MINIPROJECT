# GitHub Setup Guide

## 1. Create the repository (one team member, the owner)

1. Sign in at github.com, click **+** > **New repository**.
2. Name it `Student-Record-System` (or the name your instructor specified).
3. Choose **Private** (recommended) or Public, tick **Add a README** only if you will not push this folder's README, and click **Create repository**.

## 2. Add every team member as a collaborator

**Web:**

1. Open the repository > **Settings** > **Collaborators** (under Access).
2. Click **Add people**, enter each teammate's GitHub username or email, and choose the user.
3. Each teammate gets an email and a notification: they must **accept the invitation** (link in email, or github.com/notifications).
4. Repeat for all remaining members. Also add your instructor/evaluator if the repository is private and they need access.

**Command line (GitHub CLI):**

```bash
gh api -X PUT repos/<OWNER>/Student-Record-System/collaborators/<USERNAME> -f permission=push
```

Run once per teammate. Check with `gh api repos/<OWNER>/Student-Record-System/collaborators --jq '.[].login'`.

## 3. Push this folder (owner, first time)

```bash
cd Student-Record-System
git init
git add .
git commit -m "Add SRS, Test Plan, test cases, and RTM"
git branch -M main
git remote add origin https://github.com/<OWNER>/Student-Record-System.git
git push -u origin main
```

## 4. Other members: clone and set identity

```bash
git clone https://github.com/<OWNER>/Student-Record-System.git
cd Student-Record-System
git config user.name "Your Name"
git config user.email "the-email-linked-to-your-github-account"
```

Use the email linked to your GitHub account so your commits are credited to you (evaluators often check each member's contributions).

## 5. Daily workflow

```bash
git pull
git checkout -b feature/<short-name>
# make changes
git add .
git commit -m "Clear message about what changed"
git push -u origin feature/<short-name>
```

Open a **Pull Request** on GitHub, have a teammate review it, then merge. Always `git pull` before starting work to avoid conflicts.

## 6. Before submitting

- [ ] All members show under Settings > Collaborators (status: accepted, not pending)
- [ ] Every member has made at least one commit
- [ ] `README.md` has team names, USNs, and GitHub usernames filled in
- [ ] Names filled in on the cover page and roles table of the Test Plan and SRS
- [ ] Repository is accessible to the evaluator (public, or evaluator added)
- [ ] Repository link copied and submitted
