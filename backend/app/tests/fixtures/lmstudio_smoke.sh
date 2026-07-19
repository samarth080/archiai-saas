#!/usr/bin/env sh
# Workflow Step 0.2 smoke test — proves LM Studio enforces schema-constrained
# output BEFORE any application code depends on it. Run 5x; every run must
# return syntactically valid JSON matching the schema. Record tokens/sec from
# the LM Studio server log (expect ~25-45 tok/s on the RTX 4060 at Q4; <10
# means GPU offload silently fell back to CPU).
#
# Host: LM Studio desktop app, Developer tab -> server on :1234, model loaded
# with max GPU offload + context 4096 + "Serve on Local Network" enabled.

LLM_BASE_URL="${LLM_BASE_URL:-http://localhost:1234/v1}"

curl -s "$LLM_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "Extract the rooms requested. Respond with JSON only."},
      {"role": "user", "content": "2 bedroom flat with kitchen"}
    ],
    "temperature": 0,
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "rooms",
        "strict": true,
        "schema": {
          "type": "object",
          "properties": {
            "rooms": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "type": {"type": "string"},
                  "count": {"type": "integer"}
                },
                "required": ["type", "count"]
              }
            }
          },
          "required": ["rooms"]
        }
      }
    }
  }'
echo ""
