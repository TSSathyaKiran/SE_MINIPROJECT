#!/usr/bin/env bash
# Make the GitHub issues match docs/BACKLOG.md:
#   - issue #n gets row #n's title, body, labels and milestone (created if missing);
#     closed issues stay closed, and issues after the last row (bug reports) are left alone
# Run from the repo folder. Needs the GitHub CLI, logged in (gh auth login).
#   bash scripts/sync_issues.sh
set -euo pipefail

command -v gh >/dev/null || { echo "Install the GitHub CLI first: brew install gh && gh auth login"; exit 1; }
repo="repos/{owner}/{repo}"

for m in "Sprint 1" "Sprint 2"; do
  gh api "$repo/milestones" -f title="$m" >/dev/null 2>&1 || true
done
for l in sprint-1 sprint-2 sathya tanuj vaishnavi srujan; do
  gh label create "$l" --force --color ededed >/dev/null
done
milestone() { gh api "$repo/milestones?state=all" --jq ".[] | select(.title==\"Sprint $1\") | .number"; }
m1=$(milestone 1); m2=$(milestone 2)

trim() { sed -E 's/^ +| +$//g' <<<"$1"; }
while IFS= read -r row; do
  [[ "$row" =~ ^\|\ [0-9]+\ \| ]] || continue
  IFS='|' read -r _ num title owner sprint srs tcs _ <<<"$row"
  num=$(trim "$num"); title=$(trim "$title"); owner=$(trim "$owner")
  sprint=$(trim "$sprint"); srs=$(trim "$srs"); tcs=$(trim "$tcs")
  who=$(tr '[:upper:]' '[:lower:]' <<<"$owner")
  ms=$m2; [[ "$sprint" == 1 ]] && ms=$m1
  case "$who" in
    sathya) role="Scrum Master / Repo Owner" ;;
    tanuj) role="QA Lead / Test Engineer" ;;
    vaishnavi) role="Test Engineer" ;;
    srujan) role="Dev Lead" ;;
    *) role="Developer" ;;
  esac
  body="**Owner:** $owner ($role) · **Sprint:** $sprint
**SRS:** $srs
**Test cases:** $tcs

What to build, step by step with the commit for each step: \`docs/TEAM_GUIDE.md\`, section **#$num**."

  if gh api "$repo/issues/$num" >/dev/null 2>&1; then
    echo "Updating #$num: $title"
    gh api -X PATCH "$repo/issues/$num" -f title="$title" -f body="$body" \
      -F milestone="$ms" -f "labels[]=sprint-$sprint" -f "labels[]=$who" >/dev/null
  else
    echo "Creating: $title"
    gh issue create --title "$title" --body "$body" --label "sprint-$sprint" --label "$who" \
      --milestone "Sprint $sprint" >/dev/null
  fi
done < docs/BACKLOG.md

echo "Done. Assign each issue to its owner on GitHub."
