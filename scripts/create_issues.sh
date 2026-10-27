#!/usr/bin/env bash
# One-time: create a GitHub issue for every row in docs/BACKLOG.md, with
# sprint milestones and owner/sprint labels. Run it right after the first push
# and before anyone opens a PR, so issue #n == backlog row #n.
#
# Needs the GitHub CLI:  brew install gh && gh auth login
#   bash scripts/create_issues.sh
set -euo pipefail

command -v gh >/dev/null || { echo "Install the GitHub CLI first: brew install gh && gh auth login"; exit 1; }

existing=$(gh api "repos/{owner}/{repo}/issues?state=all&per_page=1" --jq length)
if [[ "$existing" != "0" ]]; then
  echo "This repo already has issues or PRs, so issue numbers won't match backlog numbers."
  read -r -p "Create them anyway? [y/N] " ok; [[ "$ok" == [yY] ]] || exit 1
fi

for m in "Sprint 1" "Sprint 2"; do
  gh api "repos/{owner}/{repo}/milestones" -f title="$m" >/dev/null 2>&1 || true
done
for l in sprint-1 sprint-2 tanuj sathya vaishnavi srujan; do
  gh label create "$l" --force --color ededed >/dev/null
done

trim() { sed -E 's/^ +| +$//g' <<<"$1"; }
sprint=""
while IFS= read -r row; do
  case "$row" in
    "## Sprint 1"*) sprint=1; continue ;;
    "## Sprint 2"*) sprint=2; continue ;;
  esac
  [[ "$row" =~ ^\|\ [0-9]+\ \| ]] || continue
  IFS='|' read -r _ num story owner srs tcs pts deps _ <<<"$row"
  num=$(trim "$num"); story=$(trim "$story"); owner=$(trim "$owner")
  srs=$(trim "$srs"); tcs=$(trim "$tcs"); pts=$(trim "$pts"); deps=$(trim "$deps")
  [[ "$deps" =~ ^[0-9,\ ]+$ ]] && deps=$(sed -E 's/([0-9]+)/#\1/g' <<<"$deps")
  who=$(tr '[:upper:]' '[:lower:]' <<<"${owner%% *}")

  body="Backlog row #$num (docs/BACKLOG.md)

- **Owner:** $owner
- **SRS IDs:** $srs
- **Test cases:** $tcs
- **Points:** $pts
- **Depends on:** $deps"

  echo "Creating: $story"
  gh issue create --title "$story" --body "$body" \
    --label "sprint-$sprint" --label "$who" --milestone "Sprint $sprint" >/dev/null
done < docs/BACKLOG.md

echo "Done. Assign each issue to its owner and add them to the project board."
