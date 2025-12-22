#!/usr/bin/env bash
set -euo pipefail

API_URL="http://81.177.135.202:5010/api/v1/huCYGnamm3DCdkHfSq8r/telemetry"
INTERVAL=10

send_payload() {
  local temperature humidity payload response
  read -r temperature humidity <<< "$(python - <<'PY'
import random
print(f"{22 + random.uniform(-0.4, 0.4):.1f}", f"{27 + random.uniform(-0.8, 0.8):.1f}")
PY
)"
  payload="{\"temperature\":${temperature},\"humidity\":${humidity}}"
  echo "$(date --iso-8601=seconds) INFO sending ${payload}"
  if response=$(curl -sSf -X POST "${API_URL}" \
    --header "Content-Type:application/json" \
    --data "${payload}" ); then
    echo "$(date --iso-8601=seconds) INFO request succeeded: ${response}"
  else
    echo "$(date --iso-8601=seconds) ERROR request failed" >&2
    return 1
  fi
}

while true; do
  send_payload
  sleep "${INTERVAL}"
done
