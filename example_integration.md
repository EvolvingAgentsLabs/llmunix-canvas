# Integration with LLMunix

This file shows how to configure LLMunix to use the Canvas MCP server as a real-time monitoring and visualization dashboard.

## 1. Update LLMunix settings.json

Add the following to your `llmunix/.gemini/settings.json` file:

```json
{
  "mcpServers": {
    "llmunix_canvas": {
      "command": "/path/to/your/llmunix-canvas/venv/bin/python",
      "args": ["app.py"],
      "cwd": "/path/to/your/llmunix-canvas/"
    }
  }
}
```

## 2. Send an Initial State Snapshot

To provide the Canvas with the initial state of LLMunix when it starts up, add the following to your boot script:

```markdown
#### llmunix-boot
`sh`
```sh
#!/bin/bash

# ... existing boot code ...

# --- CANVAS INSTRUMENTATION ---
# Send a full snapshot of the system state at startup

# Build a workspace file tree (example using find & jq)
WORKSPACE_TREE=$(find ~/.llmunix/workspace -type f -o -type d | jq -R -s 'split("\n") | map(select(length > 0)) | {"workspace": .}' | jq -c .)

# Build memory snapshots
PERM_MEMORY_JSON=$(find ~/.llmunix/memory/permanent -type f -exec basename {} \; | xargs -I {} cat ~/.llmunix/memory/permanent/{} | jq -R -s 'split("\n") | map(select(length > 0)) | {"content": .}' | jq -c .)
TASK_MEMORY_JSON=$(find ~/.llmunix/memory/task -type f -exec basename {} \; | xargs -I {} cat ~/.llmunix/memory/task/{} | jq -R -s 'split("\n") | map(select(length > 0)) | {"content": .}' | jq -c .)
VOL_MEMORY_JSON="{}"

# Send the snapshot to Canvas
REPORT_PAYLOAD=$(jq -n \
  --arg workspace "$WORKSPACE_TREE" \
  --argjson perm "$PERM_MEMORY_JSON" \
  --argjson task "$TASK_MEMORY_JSON" \
  --argjson vol "$VOL_MEMORY_JSON" \
  '{"fn_index": 0, "data": [$workspace, $perm, $task, $vol], "session_hash": "dummy"}')

curl -s -X POST http://localhost:7860/run/canvas_full_state_snapshot -H "Content-Type: application/json" -d "$REPORT_PAYLOAD" > /dev/null
```
```

## 3. Update LLMunix Virtual Tools

Here's how to update the key LLMunix tools to report their actions to the Canvas:

```markdown
#### memory_store
`sh`
```sh
#!/bin/bash
set -e

MEMORY_TYPE="$1"
KEY="$2"
VALUE="$3"

# Original LLMunix memory storage logic
MEMORY_DIR=~/.llmunix/memory/${MEMORY_TYPE}
mkdir -p "$MEMORY_DIR"
echo "$VALUE" > "$MEMORY_DIR/$KEY"

# --- CANVAS INSTRUMENTATION ---
# Report to Canvas MCP server
REPORT_PAYLOAD=$(jq -n \
  --arg type "$MEMORY_TYPE" \
  --arg key "$KEY" \
  --arg value "$VALUE" \
  '{ "fn_index": 0, "data": [ $type, $key, $value ], "session_hash": "dummy" }')

# Call the MCP tool via its standard API endpoint exposed by Gradio
curl -s -X POST http://localhost:7860/run/canvas_report_memory_write -H "Content-Type: application/json" -d "$REPORT_PAYLOAD" > /dev/null

echo "Stored in $MEMORY_TYPE memory: $KEY"
```
```

### 3.1 Memory Store Tool

```markdown
#### memory_store
`sh`
```sh
#!/bin/bash
set -e

MEMORY_TYPE="$1"
KEY="$2"
VALUE="$3"

# Original LLMunix memory storage logic
MEMORY_DIR=~/.llmunix/memory/${MEMORY_TYPE}
mkdir -p "$MEMORY_DIR"
echo "$VALUE" > "$MEMORY_DIR/$KEY"

# --- CANVAS INSTRUMENTATION ---
# Report to Canvas MCP server
REPORT_PAYLOAD=$(jq -n \
  --arg type "$MEMORY_TYPE" \
  --arg key "$KEY" \
  --arg value "$VALUE" \
  '{ "fn_index": 0, "data": [ $type, $key, $value ], "session_hash": "dummy" }')

# Call the MCP tool via its standard API endpoint exposed by Gradio
curl -s -X POST http://localhost:7860/run/canvas_report_memory_write -H "Content-Type: application/json" -d "$REPORT_PAYLOAD" > /dev/null

echo "Stored in $MEMORY_TYPE memory: $KEY"
```
```

### 3.2 Write File Tool

```markdown
#### write_file
`sh`
```sh
#!/bin/bash
set -e

FILE_PATH="$1"
CONTENT="$2"

# Original file writing logic
mkdir -p "$(dirname "$FILE_PATH")"
echo "$CONTENT" > "$FILE_PATH"

# --- CANVAS INSTRUMENTATION ---
# Report file update to Canvas
REPORT_PAYLOAD=$(jq -n \
  --arg path "$FILE_PATH" \
  --arg content "$CONTENT" \
  '{ "fn_index": 0, "data": [ $path, $content ], "session_hash": "dummy" }')

curl -s -X POST http://localhost:7860/run/canvas_report_file_update -H "Content-Type: application/json" -d "$REPORT_PAYLOAD" > /dev/null

echo "File written: $FILE_PATH"
```
```

### 3.3 Send Message Tool

```markdown
#### send_message
`sh`
```sh
#!/bin/bash
set -e

FROM_AGENT="$1"
TO_AGENT="$2"
PRIORITY="$3"
MESSAGE="$4"

# Original message sending logic
MESSAGE_DIR=~/.llmunix/messages/$TO_AGENT
mkdir -p "$MESSAGE_DIR"
TIMESTAMP=$(date +%s)
echo "$FROM_AGENT|$PRIORITY|$MESSAGE" > "$MESSAGE_DIR/$TIMESTAMP"

# --- CANVAS INSTRUMENTATION ---
# Report message to Canvas
REPORT_PAYLOAD=$(jq -n \
  --arg from "$FROM_AGENT" \
  --arg to "$TO_AGENT" \
  --arg msg "$MESSAGE" \
  --arg pri "$PRIORITY" \
  '{ "fn_index": 0, "data": [ $from, $to, $msg, $pri ], "session_hash": "dummy" }')

curl -s -X POST http://localhost:7860/run/canvas_report_message_sent -H "Content-Type: application/json" -d "$REPORT_PAYLOAD" > /dev/null

echo "Message sent from $FROM_AGENT to $TO_AGENT"
```
```

### 3.4 Agent Step Reporting

To report agent steps to the Canvas, add similar instrumentation to your agent tools:

```sh
# After executing a tool
AGENT_NAME="SystemAgent"  # Or the current agent name
THOUGHT="I need to search for X"
TOOL_CALL="search('term')"

REPORT_PAYLOAD=$(jq -n \
  --arg agent "$AGENT_NAME" \
  --arg thought "$THOUGHT" \
  --arg tool "$TOOL_CALL" \
  '{ "fn_index": 0, "data": [ $agent, $thought, $tool ], "session_hash": "dummy" }')

curl -s -X POST http://localhost:7860/run/canvas_report_step -H "Content-Type: application/json" -d "$REPORT_PAYLOAD" > /dev/null
```

## 4. Running the System

1. Start the Canvas server:
   ```
   cd llmunix-canvas
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```

2. Open the Canvas UI in your browser at: http://localhost:7860

3. Start LLMunix CLI in another terminal and run missions to see them visualized in the Canvas UI.

## 5. Features Visualization Guide

### Dashboard View

The dashboard provides a real-time graph visualization of agents and their interactions. Agents appear as green nodes, while tools they call appear as blue nodes. The visualization is interactive - you can zoom, pan, and click on nodes to focus on specific agents.

### Memory View

The Memory tab shows the contents of all three memory tiers:

- **Permanent Memory**: Long-term knowledge that persists across tasks
- **Task Memory**: Memory specific to the current task or mission
- **Volatile Memory**: Temporary data that doesn't persist between sessions

### Messages View

The Messages tab provides a Slack-like interface showing communication between agents, with priority indicators and timestamps.

### Workspace View

The Workspace tab displays the current state of the file system, showing recently updated files and their contents.