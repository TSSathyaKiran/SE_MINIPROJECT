#!/usr/bin/env bash
# Git shortcuts for the SRS-App team.
# Works on macOS/Linux and in Git Bash on Windows. <n> is the GitHub issue number.
#
#   bash scripts/g.sh start 12 student-create        new branch feature/12-student-create from latest main
#   bash scripts/g.sh start 12 lockout-bug fix       same, but fix/12-lockout-bug   (feature | fix | test)
#   bash scripts/g.sh commit feat auth "add POST /auth/login with bcrypt check"
#                                                    -> commits "feat(auth): add POST /auth/login with bcrypt check (#12)"
#   bash scripts/g.sh push                           push your branch and print the "open PR" link
#   bash scripts/g.sh sync                           merge the latest main into your branch
set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }
branch() { git branch --show-current; }
issue_no() { branch | sed -nE 's#^(feature|fix|test)/([0-9]+)-.*#\2#p'; }

cmd_start() {
  local n="${1:-}" name="${2:-}" kind="${3:-feature}"
  [[ "$n" =~ ^[0-9]+$ && "$name" =~ ^[a-z0-9-]+$ ]] \
    || die "usage: start <issue-number> <short-name-in-lowercase-with-dashes> [feature|fix|test]"
  case "$kind" in feature|fix|test) ;; *) die "branch type must be feature, fix or test" ;; esac
  [[ -z "$(git status --porcelain)" ]] || die "you have uncommitted changes; commit them first"
  git checkout main
  git pull --ff-only origin main
  git checkout -b "$kind/$n-$name"
  echo
  echo "On $kind/$n-$name. Move issue #$n to In Progress on the project board."
}

cmd_commit() {
  local type="${1:-}" module="${2:-}" msg="${3:-}"
  [[ -n "$type" && -n "$module" && -n "$msg" ]] || die 'usage: commit <type> <module> "<what changed>"'
  case "$type" in feat|fix|test|docs|refactor|chore|ci) ;;
    *) die "type must be one of: feat fix test docs refactor chore ci" ;; esac
  [[ "$(branch)" != "main" ]] || die "you're on main; start a branch first: bash scripts/g.sh start <n> <name>"
  local n; n=$(issue_no)
  [[ -n "$n" ]] || die "branch '$(branch)' isn't named like feature/<issue-number>-name"
  (( ${#msg} <= 72 )) || die "message is ${#msg} characters; keep it to 72 or less"
  [[ -n "$(git status --porcelain)" ]] || die "nothing to commit"

  # Same check CI runs. Exit code 5 means "no tests yet", which is fine.
  if [[ -z "${SKIP_TESTS:-}" ]] && command -v pytest >/dev/null; then
    local rc=0
    pytest -q tests --ignore=tests/ui --ignore=tests/performance --ignore=tests/security || rc=$?
    [[ $rc -eq 0 || $rc -eq 5 ]] || die "tests fail; fix them first (or SKIP_TESTS=1 for a docs-only commit)"
  fi

  local line="$type($module): $msg (#$n)"
  echo
  git status --short
  echo
  echo "Commit message: $line"
  local ok; read -r -p "Commit all files above? [y/N] " ok
  [[ "$ok" == [yY] ]] || { echo "Cancelled, nothing committed."; exit 1; }
  git add -A
  git commit -m "$line"
}

cmd_push() {
  local b; b=$(branch)
  [[ "$b" != "main" ]] || die "main only changes through pull requests"
  git push -u origin "$b"
  local url; url=$(git remote get-url origin)
  url=${url%.git}; url=${url/git@github.com:/https://github.com/}
  echo
  echo "Open the PR:  $url/compare/main...$b?expand=1"
  echo "Keep 'Closes #$(issue_no)' in the PR text, request a reviewer, move the card to In Review."
}

cmd_sync() {
  [[ -z "$(git status --porcelain)" ]] || die "you have uncommitted changes; commit them first"
  git pull --no-rebase origin main
}

cmd="${1:-}"; shift || true
case "$cmd" in
  start)  cmd_start "$@" ;;
  commit) cmd_commit "$@" ;;
  push)   cmd_push ;;
  sync)   cmd_sync ;;
  *) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
