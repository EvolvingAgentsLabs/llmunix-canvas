import gradio as gr

# This class will hold the live state of the LLMunix session.
# Using a class ensures all UI components and tool handlers share the same data.
class CanvasState:
    def __init__(self):
        # The agent interaction graph data
        self.graph = gr.State({"nodes": set(), "edges": []})
        
        # The raw data for UI components
        self.workspace_html = gr.State("")
        self.permanent_memory_md = gr.State("### Permanent Memory\n---")
        self.task_memory_md = gr.State("### Task Memory\n---")
        self.volatile_memory_md = gr.State("### Volatile Memory\n---")
        self.messages_md = gr.State("### Agent Messages\n---")
        
        # State JSON for JavaScript frontend
        self.state_json = gr.State("{}")

# Instantiate a single global state object
canvas_state = CanvasState()