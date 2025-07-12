#!/usr/bin/env python3
"""
Test script to simulate MCP calls to the Canvas server.
Run this while the app.py server is running to see updates in the UI.
"""

import requests
import time
import json
import random

def call_mcp_endpoint(endpoint, data):
    """Call a MCP endpoint on the Gradio server"""
    url = f"http://localhost:7860/run/{endpoint}"
    payload = {
        "data": data,
        "session_hash": "test_session"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Successfully called {endpoint}: {response.json()}")
    else:
        print(f"Error calling {endpoint}: {response.status_code}")
        print(response.text)

def send_initial_state_snapshot():
    """Send a full snapshot of the system state to initialize the UI"""
    print("Sending initial state snapshot...")
    
    # Create a simple workspace file tree structure in JSON
    workspace_tree = json.dumps({
        "workspace": {
            "agents": ["SystemAgent.py", "SearchAgent.py", "CodeAgent.py"],
            "tasks": {
                "visualization_task": ["plan.md", "requirements.txt"]
            },
            "output": ["report.md"]
        }
    })
    
    # Create memory snapshots
    permanent_memory = {
        "user_preferences": "The user prefers detailed explanations and has experience with Python.",
        "system_config": "System is running on macOS with Python 3.9."
    }
    
    task_memory = {
        "current_task": "Create a data visualization example using Python libraries.",
        "deadline": "2025-07-15"
    }
    
    volatile_memory = {
        "session_id": "test-session-123",
        "start_time": "2025-07-12T10:00:00"
    }
    
    # Send the snapshot to Canvas
    call_mcp_endpoint("canvas_full_state_snapshot", [
        workspace_tree,
        permanent_memory,
        task_memory,
        volatile_memory
    ])
    time.sleep(2)  # Give the UI time to update

def simulate_agent_workflow():
    """Simulate a sequence of agent actions to demonstrate Canvas functionality"""
    print("Starting agent simulation...")
    
    # First send an initial state snapshot
    send_initial_state_snapshot()
    
    # Simulate SystemAgent starting up
    call_mcp_endpoint("canvas_report_step", [
        "SystemAgent", 
        "Starting up and checking the task", 
        "check_task()"
    ])
    time.sleep(1)
    
    # Simulate memory write to permanent memory
    call_mcp_endpoint("canvas_report_memory_write", [
        "permanent", 
        "user_preferences", 
        "The user prefers detailed explanations and has experience with Python."
    ])
    time.sleep(1)
    
    # Simulate file update
    call_mcp_endpoint("canvas_report_file_update", [
        "/workspace/tasks/visualization_task/plan.md",
        "# Visualization Task Plan\n\n1. Research visualization libraries\n2. Select appropriate library for the task\n3. Create example code\n4. Generate output report"
    ])
    time.sleep(1)
    
    # Simulate SystemAgent delegating to SearchAgent
    call_mcp_endpoint("canvas_report_step", [
        "SystemAgent", 
        "I need to search for information about Python libraries", 
        "delegate('SearchAgent')"
    ])
    time.sleep(1)
    
    # Simulate message between agents
    call_mcp_endpoint("canvas_report_message_sent", [
        "SystemAgent",
        "SearchAgent",
        "Please search for Python visualization libraries and report back.",
        "high"
    ])
    time.sleep(1)
    
    # Simulate SearchAgent actions
    call_mcp_endpoint("canvas_report_step", [
        "SearchAgent", 
        "Searching for information about Python libraries", 
        "search('Python libraries for data visualization')"
    ])
    time.sleep(1)
    
    # Simulate memory write to task memory
    call_mcp_endpoint("canvas_report_memory_write", [
        "task", 
        "search_results", 
        "Found matplotlib, seaborn, plotly, and bokeh as popular Python data visualization libraries."
    ])
    time.sleep(1)
    
    # Simulate volatile memory write
    call_mcp_endpoint("canvas_report_memory_write", [
        "volatile", 
        "search_time", 
        "0.45 seconds"
    ])
    time.sleep(1)
    
    # Simulate SearchAgent reporting back to SystemAgent
    call_mcp_endpoint("canvas_report_message_sent", [
        "SearchAgent",
        "SystemAgent",
        "Found several visualization libraries: matplotlib, seaborn, plotly, and bokeh.",
        "normal"
    ])
    time.sleep(1)
    
    # Simulate SystemAgent delegating to CodeAgent
    call_mcp_endpoint("canvas_report_step", [
        "SystemAgent", 
        "Now I need to write some sample visualization code", 
        "delegate('CodeAgent')"
    ])
    time.sleep(1)
    
    # Simulate message to CodeAgent
    call_mcp_endpoint("canvas_report_message_sent", [
        "SystemAgent",
        "CodeAgent",
        "Please write a sample visualization using matplotlib based on the search results.",
        "normal"
    ])
    time.sleep(1)
    
    # Simulate CodeAgent actions
    call_mcp_endpoint("canvas_report_step", [
        "CodeAgent", 
        "Writing sample matplotlib visualization code", 
        "write_code('example_visualization.py')"
    ])
    time.sleep(1)
    
    # Simulate file update with code
    python_code = """import matplotlib.pyplot as plt\nimport numpy as np\n\n# Generate data\nx = np.linspace(0, 10, 100)\ny = np.sin(x)\n\n# Create plot\nplt.figure(figsize=(10, 6))\nplt.plot(x, y, '-b', label='sin(x)')\nplt.title('Simple Sine Wave')\nplt.xlabel('x')\nplt.ylabel('sin(x)')\nplt.grid(True)\nplt.legend()\n\n# Save the figure\nplt.savefig('sine_wave.png')\nplt.close()\n\nprint("Plot generated successfully!")\n"""
    
    call_mcp_endpoint("canvas_report_file_update", [
        "/workspace/tasks/visualization_task/example_visualization.py",
        python_code
    ])
    time.sleep(1)
    
    # Simulate message back to SystemAgent
    call_mcp_endpoint("canvas_report_message_sent", [
        "CodeAgent",
        "SystemAgent",
        "Code for matplotlib visualization has been created. It generates a sine wave plot.",
        "normal"
    ])
    time.sleep(1)
    
    # Simulate SystemAgent creating a report
    call_mcp_endpoint("canvas_report_step", [
        "SystemAgent", 
        "Creating final report", 
        "write_file('report.md')"
    ])
    time.sleep(1)
    
    # Simulate file update with report
    call_mcp_endpoint("canvas_report_file_update", [
        "/workspace/output/report.md",
        "# Data Visualization Task Report\n\n## Libraries Explored\n- matplotlib\n- seaborn\n- plotly\n- bokeh\n\n## Selected Library\nFor this task, matplotlib was selected because of its simplicity and wide adoption.\n\n## Implementation\nA simple sine wave visualization was created. The code is available in `example_visualization.py`.\n\n## Next Steps\nFuture work could include more complex visualizations using interactive libraries like plotly.\n"
    ])
    time.sleep(1)
    
    # Simulate completion
    call_mcp_endpoint("canvas_report_step", [
        "SystemAgent", 
        "Task completed successfully", 
        "complete_task()"
    ])
    time.sleep(1)
    
    # Broadcast message to all agents
    call_mcp_endpoint("canvas_report_message_sent", [
        "SystemAgent",
        "all",
        "Visualization task has been completed successfully. Thank you for your contributions.",
        "low"
    ])
    
    print("Simulation completed!")

def run_advanced_simulation():
    """Run a more comprehensive simulation with parallel agent activities"""
    # This is a placeholder for a more complex simulation scenario
    # In a real implementation, you might want to simulate multiple agents
    # working in parallel on different tasks
    pass

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--advanced":
        run_advanced_simulation()
    else:
        simulate_agent_workflow()