# LLMunix Canvas

A visualization and monitoring dashboard for the LLMunix system built with Python/Gradio as an MCP server.

## Features

- Real-time agent graph visualization
- Memory monitoring (permanent and task memory)
- Agent message timeline
- Workspace file tree visualization

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/llmunix-canvas.git
cd llmunix-canvas

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. **Start the Canvas Server:**

```bash
python app.py
```

This will start the Gradio server on http://localhost:7860

2. **Open the Canvas UI:**

Open your web browser and navigate to http://localhost:7860

3. **Integrate with LLMunix:**

Follow the instructions in `example_integration.md` to configure LLMunix to communicate with the Canvas server.

## Testing

To test the Canvas functionality without LLMunix integration:

```bash
python test_mcp.py
```

This will send simulated MCP calls to the Canvas server to demonstrate its functionality.

## Directory Structure

```
llmunix-canvas/
├── app.py              # Main Gradio application
├── state.py            # Canvas state management
├── components/         # UI components
│   └── agent_graph.py  # Graph visualization component
├── test_mcp.py         # Test script for MCP functionality
└── requirements.txt    # Python dependencies
```

## Integration with LLMunix

See `example_integration.md` for detailed instructions on integrating LLMunix with Canvas.