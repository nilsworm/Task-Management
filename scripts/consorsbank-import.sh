#!/bin/zsh
# Watches ~/Downloads for new Consorsbank CSVs and POSTs them to the cost import API.
# Credentials are read from ~/.consorsbank-import.env (not in repo).

ENV_FILE="$HOME/.consorsbank-import.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy scripts/consorsbank-import.env.example and fill in your values." >&2
  exit 1
fi
source "$ENV_FILE"

STATE_FILE="$HOME/.consorsbank-last-import"

latest=$(ls -t ~/Downloads/*consorsbank*.csv 2>/dev/null | head -1)
[[ -z "$latest" ]] && exit 0

[[ -f "$STATE_FILE" ]] && [[ "$(cat "$STATE_FILE")" == "$latest" ]] && exit 0

result=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Basic $(echo -n "$API_AUTH" | base64)" \
  -F "file=@$latest;filename=$(basename "$latest")")

imported=$(echo "$result" | /usr/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('imported',0))" 2>/dev/null)
skipped=$(echo "$result"  | /usr/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('skipped',0))" 2>/dev/null)

echo "$latest" > "$STATE_FILE"
osascript -e "display notification \"Importiert: $imported | Übersprungen: $skipped\" with title \"Consorsbank Import\" sound name \"Glass\""
