#!/bin/bash
# Reusable DeepSeek API caller via OpenRouter
# Usage: ./deepseek_call.sh "your prompt here"

# Check if prompt was provided
if [ -z "$1" ]; then
    echo "Error: No prompt provided"
    echo "Usage: ./deepseek_call.sh \"your prompt here\""
    exit 1
fi

PROMPT="$1"
API_KEY="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"
MODEL="deepseek/deepseek-chat-v3.1"
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"

# Create temporary JSON file (still need this for complex prompts)
TEMP_FILE="$(dirname "$0")/temp_request_$$.json"

# Build JSON request
cat > "$TEMP_FILE" <<EOF
{
  "model": "$MODEL",
  "messages": [
    {
      "role": "user",
      "content": $(echo "$PROMPT" | jq -Rs . 2>/dev/null || echo "\"$PROMPT\"")
    }
  ],
  "temperature": 0.3
}
EOF

# Make API call
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @"$TEMP_FILE")

# Clean up temp file
rm -f "$TEMP_FILE"

# Extract content from response
if command -v jq &> /dev/null; then
    echo "$RESPONSE" | jq -r '.choices[0].message.content'
else
    # Simple extraction without jq (less reliable but works)
    echo "$RESPONSE" | grep -oP '(?<="content":")[^"]*(?=")' | head -1
fi
