import gradio as gr
from state import canvas_state
import datetime
import json
from components.agent_graph import create_agent_graph_image, create_state_json

# --- UI Component Rendering Functions ---
# These functions don't take inputs; they just read from the shared state.

def render_workspace():
    # In a real app, this would parse a file tree object.
    # For the prototype, we just return the raw HTML string from the state.
    return canvas_state.workspace_html.value

def render_agent_graph():
    # Use the visualization component for a graphical representation
    nodes = canvas_state.graph.value["nodes"]
    edges = canvas_state.graph.value["edges"]
    
    # Only create visualization if we have nodes
    if nodes:
        # Generate the graph visualization
        return create_agent_graph_image(nodes, edges)
    else:
        # If no data yet, return a placeholder
        return "<p>No agent interactions recorded yet.</p>"

def render_permanent_memory():
    return canvas_state.permanent_memory_md.value

def render_task_memory():
    return canvas_state.task_memory_md.value

def render_messages():
    return canvas_state.messages_md.value

# --- MCP Tool Implementations (API Endpoints) ---
# These functions are the "instrumentation hooks". They are NOT displayed in the UI.
# Their only job is to update the shared `canvas_state`.

def report_agent_step(agent_name: str, thought: str, tool_call: str) -> str:
    """MCP Tool: Reports an agent's thought process and action."""
    graph = canvas_state.graph.value
    
    # Add nodes to the graph if they don't exist
    graph["nodes"].add(agent_name)
    
    # A simple way to represent the tool call as a node
    tool_node = f"`{tool_call.split('(')[0]}`"
    graph["nodes"].add(tool_node)
    
    # Add an edge from the agent to the tool it called
    graph["edges"].append((agent_name, tool_node))
    
    # This is not thread-safe, but sufficient for a single-user prototype
    canvas_state.graph.value = graph
    
    # Update the messages display
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"### {timestamp} - {agent_name}\n**Thought:** {thought}\n**Action:** {tool_call}\n---\n"
    canvas_state.messages_md.value = entry + canvas_state.messages_md.value
    
    return f"Step from {agent_name} reported to Canvas."


def report_memory_write(tier: str, key: str, value: str) -> str:
    """MCP Tool: Reports a write to the memory system."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"- **{timestamp} [{key}]**: {value[:100]}...\n"
    
    if tier == "permanent":
        canvas_state.permanent_memory_md.value += entry
    elif tier == "task":
        canvas_state.task_memory_md.value += entry
    elif tier == "volatile":
        # Add support for volatile memory
        if not hasattr(canvas_state, 'volatile_memory_md'):
            canvas_state.volatile_memory_md = gr.State("### Volatile Memory\n---")
        canvas_state.volatile_memory_md.value += entry
        
    return f"Memory write to '{tier}' tier reported."


def report_file_update(path: str, content: str) -> str:
    """MCP Tool: Reports that a file has been written or updated."""
    # This is a simplification. A real implementation would need to handle
    # the entire file tree. For now, we just show the latest updated file.
    html_content = f"<h4>Last Updated: {path}</h4><pre><code>{content}</code></pre>"
    canvas_state.workspace_html.value = html_content
    return f"File update for {path} reported to Canvas."


def report_message_sent(from_agent: str, to_agent: str, message: str, priority: str = "normal") -> str:
    """MCP Tool: Reports a message sent between agents."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Update the graph to show message passing
    graph = canvas_state.graph.value
    graph["nodes"].add(from_agent)
    graph["nodes"].add(to_agent)
    # Add an edge for the message
    graph["edges"].append((from_agent, to_agent))
    canvas_state.graph.value = graph

    # Update the message log
    entry = f"- **{timestamp} [{priority.upper()}] {from_agent} → {to_agent}**: {message}\n"
    canvas_state.messages_md.value = entry + canvas_state.messages_md.value
    return "Message reported."


def full_state_snapshot(workspace_tree: str, permanent_memory: dict, task_memory: dict, volatile_memory: dict = None) -> str:
    """MCP Tool: Receives a full snapshot of the LLMunix state at startup."""
    # Parse the workspace tree (JSON string of the file structure)
    try:
        tree_data = json.loads(workspace_tree)
        html_content = "<h3>Workspace Files</h3><ul>"
        
        def render_tree_node(node, path=""):
            nonlocal html_content
            if isinstance(node, dict):
                # It's a directory
                for name, child in node.items():
                    new_path = f"{path}/{name}" if path else name
                    html_content += f"<li><strong>{name}/</strong><ul>"
                    render_tree_node(child, new_path)
                    html_content += "</ul></li>"
            elif isinstance(node, list):
                # It's a list of files
                for file in node:
                    html_content += f"<li>{file}</li>"
        
        render_tree_node(tree_data)
        html_content += "</ul>"
        canvas_state.workspace_html.value = html_content
    except Exception as e:
        return f"Error parsing workspace tree: {str(e)}"
    
    # Parse memory dictionaries
    try:
        if permanent_memory:
            perm_content = "### Permanent Memory\n---\n"
            for key, value in permanent_memory.items():
                perm_content += f"- **[{key}]**: {value[:100]}...\n"
            canvas_state.permanent_memory_md.value = perm_content
            
        if task_memory:
            task_content = "### Task Memory\n---\n"
            for key, value in task_memory.items():
                task_content += f"- **[{key}]**: {value[:100]}...\n"
            canvas_state.task_memory_md.value = task_content
            
        if volatile_memory:
            volatile_content = "### Volatile Memory\n---\n"
            for key, value in volatile_memory.items():
                volatile_content += f"- **[{key}]**: {value[:100]}...\n"
            canvas_state.volatile_memory_md.value = volatile_content
    except Exception as e:
        return f"Error parsing memory data: {str(e)}"
    
    return "Full state snapshot received."


# Function to generate the complete state JSON for the frontend
def get_full_state_json():
    state_json = create_state_json(
        canvas_state.graph.value,
        canvas_state.workspace_html.value,
        canvas_state.permanent_memory_md.value,
        canvas_state.task_memory_md.value,
        canvas_state.volatile_memory_md.value,
        canvas_state.messages_md.value
    )
    canvas_state.state_json.value = state_json
    return state_json

# Define the Gradio UI layout with enhanced JavaScript frontend
with gr.Blocks(title="LLMunix Canvas") as demo:
    # Custom CSS and JavaScript setup
    gr.HTML("""
    <head>
        <title>LLMunix Canvas</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .container { display: flex; flex-direction: column; height: 100vh; }
            .header { padding: 10px; background-color: #2a3d66; color: white; }
            .main { display: flex; flex: 1; overflow: hidden; }
            .left-panel { width: 300px; overflow-y: auto; padding: 10px; background-color: #f5f5f5; }
            .right-panel { flex: 1; overflow-y: auto; padding: 10px; }
            .memory-section { margin-bottom: 20px; }
            .memory-section h3 { margin-top: 0; padding-bottom: 5px; border-bottom: 1px solid #ddd; }
            .agent-network { width: 100%; height: 600px; border: 1px solid #ddd; background-color: white; }
            .messages { height: 300px; overflow-y: auto; padding: 10px; background-color: white; border: 1px solid #ddd; }
            .tabs { display: flex; }
            .tab { padding: 10px 15px; cursor: pointer; background-color: #f1f1f1; border: 1px solid #ddd; }
            .tab.active { background-color: white; border-bottom: none; }
            .tab-content { display: none; padding: 15px; border: 1px solid #ddd; border-top: none; }
            .tab-content.active { display: block; }
        </style>
        <!-- Load vis.js from CDN -->
        <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    </head>
    <div class="container">
        <div class="header">
            <h2>LLMunix Canvas</h2>
        </div>
        <div class="tabs">
            <div class="tab active" onclick="switchTab('dashboard')">Dashboard</div>
            <div class="tab" onclick="switchTab('memory')">Memory</div>
            <div class="tab" onclick="switchTab('messages')">Messages</div>
            <div class="tab" onclick="switchTab('workspace')">Workspace</div>
        </div>
        <div class="tab-content active" id="dashboard">
            <div class="agent-network" id="agent-network"></div>
        </div>
        <div class="tab-content" id="memory">
            <div class="memory-section">
                <h3>Permanent Memory</h3>
                <div id="permanent-memory" class="memory-content"></div>
            </div>
            <div class="memory-section">
                <h3>Task Memory</h3>
                <div id="task-memory" class="memory-content"></div>
            </div>
            <div class="memory-section">
                <h3>Volatile Memory</h3>
                <div id="volatile-memory" class="memory-content"></div>
            </div>
        </div>
        <div class="tab-content" id="messages">
            <div class="messages" id="agent-messages"></div>
        </div>
        <div class="tab-content" id="workspace">
            <div id="workspace-content"></div>
        </div>
    </div>
    <script type="text/javascript">
        // Tab switching logic
        function switchTab(tabId) {
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Deactivate all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Activate the selected tab and content
            document.getElementById(tabId).classList.add('active');
            const selectedTab = Array.from(tabs).find(tab => tab.textContent.toLowerCase().includes(tabId));
            if (selectedTab) selectedTab.classList.add('active');
        }
        
        // Network visualization instance
        let network = null;
        
        // Initialize the network visualization
        function initNetwork(data) {
            const container = document.getElementById('agent-network');
            const options = {
                nodes: {
                    shape: 'box',
                    margin: 10,
                    font: { size: 14 },
                    borderWidth: 2,
                    shadow: true,
                    groups: {
                        agent: { color: { background: '#c8e6c9', border: '#4caf50' } },
                        tool: { color: { background: '#bbdefb', border: '#2196f3' } }
                    }
                },
                edges: {
                    width: 2,
                    smooth: {
                        type: 'dynamic',
                        roundness: 0.5
                    },
                    arrows: {
                        to: { enabled: true, scaleFactor: 1 }
                    }
                },
                physics: {
                    stabilization: {
                        enabled: true,
                        iterations: 100
                    },
                    solver: 'forceAtlas2Based'
                },
                layout: {
                    improvedLayout: true
                }
            };
            
            // Initialize or update the network
            if (network === null) {
                network = new vis.Network(container, data, options);
            } else {
                // Update existing network
                network.setData(data);
            }
        }
        
        // Markdown rendering helper (simple version)
        function renderMarkdown(markdown) {
            // Very basic markdown rendering for this example
            let html = markdown
                .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                .replace(/\*\*(.*)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>')
                .replace(/- (.*)/g, '<li>$1</li>');
                
            return html;
        }
        
        // Update the UI with the latest state
        function updateUI(state) {
            // Update graph visualization
            initNetwork(state.graph);
            
            // Update memory sections
            document.getElementById('permanent-memory').innerHTML = renderMarkdown(state.memory.permanent);
            document.getElementById('task-memory').innerHTML = renderMarkdown(state.memory.task);
            document.getElementById('volatile-memory').innerHTML = renderMarkdown(state.memory.volatile);
            
            // Update messages
            document.getElementById('agent-messages').innerHTML = renderMarkdown(state.messages);
            
            // Update workspace
            document.getElementById('workspace-content').innerHTML = state.workspace;
        }
    </script>
    """)
    
    # Hidden textbox to hold the JSON state for the JavaScript frontend
    state_json_textbox = gr.Textbox(label="state_json", elem_id="state_json", value="{}", visible=False)
            
    # --- Define the API endpoints for the MCP tools ---
    # `api_name` makes these functions available as MCP tools.
    
    # Setup the real-time state update
    demo.load(
        fn=get_full_state_json,
        inputs=None,
        outputs=state_json_textbox,
        every=1  # Poll every second
    )
    
    # Connect the JavaScript to react to state changes
    demo.js("""
    function(stateJson) {
        if (!stateJson) return;
        try {
            const state = JSON.parse(stateJson);
            updateUI(state);
        } catch (e) {
            console.error("Error parsing state JSON:", e);
        }
    }
    """, state_json_textbox)
    
    demo.queue()
    
    gr.Interface(
        fn=report_agent_step,
        inputs=[gr.Textbox(), gr.Textbox(), gr.Textbox()],
        outputs=gr.Textbox(),
        api_name="canvas_report_step"
    )
    
    gr.Interface(
        fn=report_memory_write,
        inputs=[gr.Textbox(), gr.Textbox(), gr.Textbox()],
        outputs=gr.Textbox(),
        api_name="canvas_report_memory_write"
    )
    
    gr.Interface(
        fn=report_file_update,
        inputs=[gr.Textbox(), gr.Textbox()],
        outputs=gr.Textbox(),
        api_name="canvas_report_file_update"
    )
    
    gr.Interface(
        fn=report_message_sent,
        inputs=[gr.Textbox(), gr.Textbox(), gr.Textbox(), gr.Textbox()],
        outputs=gr.Textbox(),
        api_name="canvas_report_message_sent"
    )
    
    gr.Interface(
        fn=full_state_snapshot,
        inputs=[gr.Textbox(), gr.JSON(), gr.JSON(), gr.JSON()],
        outputs=gr.Textbox(),
        api_name="canvas_full_state_snapshot"
    )

# --- Launch the Server ---
# The `launch()` method starts a FastAPI web server that serves both the
# Gradio UI and the MCP API endpoints.
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)