import json

def create_agent_graph_image(nodes, edges):
    """
    Create a visualization of the agent interaction graph using vis.js.
    
    Args:
        nodes: Set of node names
        edges: List of (source, target) tuples
        
    Returns:
        HTML with vis.js network visualization
    """
    # Convert node set to list of dictionaries for vis.js
    vis_nodes = []
    for node in nodes:
        node_data = {
            "id": node,
            "label": node,
            "group": "tool" if node.startswith('`') else "agent"
        }
        vis_nodes.append(node_data)
    
    # Convert edges to vis.js format
    vis_edges = []
    for idx, (source, target) in enumerate(edges):
        edge_data = {
            "id": f"e{idx}",
            "from": source,
            "to": target,
            "arrows": "to"
        }
        vis_edges.append(edge_data)
    
    # Create JSON data for vis.js
    graph_data = {
        "nodes": vis_nodes,
        "edges": vis_edges
    }
    
    # Create HTML with embedded vis.js
    html = f"""
    <div id="agent-network" style="width: 100%; height: 600px; border: 1px solid #ddd;"></div>
    
    <script type="text/javascript">
      // Load the vis.js library if not already loaded
      if (typeof vis === 'undefined') {{
        var script = document.createElement('script');
        script.src = 'https://unpkg.com/vis-network/standalone/umd/vis-network.min.js';
        script.onload = createNetwork;
        document.head.appendChild(script);
      }} else {{
        createNetwork();
      }}
      
      function createNetwork() {{
        // Create a network
        var container = document.getElementById('agent-network');
        var data = {json.dumps(graph_data)};
        var options = {{
          nodes: {{
            shape: 'box',
            margin: 10,
            font: {{ size: 14 }},
            borderWidth: 2,
            shadow: true,
            groups: {{
              agent: {{ color: {{ background: '#c8e6c9', border: '#4caf50' }} }},
              tool: {{ color: {{ background: '#bbdefb', border: '#2196f3' }} }}
            }}
          }},
          edges: {{
            width: 2,
            smooth: {{
              type: 'dynamic',
              roundness: 0.5
            }},
            arrows: {{
              to: {{ enabled: true, scaleFactor: 1 }}
            }}
          }},
          physics: {{
            stabilization: {{
              enabled: true,
              iterations: 100
            }},
            solver: 'forceAtlas2Based'
          }},
          layout: {{
            improvedLayout: true
          }}
        }};
        
        // Initialize the network
        var network = new vis.Network(container, data, options);
        
        // Fit to viewport when first created
        network.fit();
      }}
    </script>
    """
    
    return html

def create_state_json(graph, workspace_html, permanent_memory_md, task_memory_md, volatile_memory_md, messages_md):
    """
    Create a JSON representation of the entire application state for the JavaScript frontend.
    
    Args:
        graph: The graph state object
        workspace_html: The workspace HTML content
        permanent_memory_md: Permanent memory markdown content
        task_memory_md: Task memory markdown content
        volatile_memory_md: Volatile memory markdown content
        messages_md: Agent messages markdown content
        
    Returns:
        JSON string of the application state
    """
    # Convert node set to list for JSON serialization
    nodes_list = list(graph["nodes"])
    
    # Create a complete state object
    state = {
        "graph": {
            "nodes": [
                {
                    "id": node,
                    "label": node,
                    "group": "tool" if node.startswith('`') else "agent"
                } for node in nodes_list
            ],
            "edges": [
                {
                    "from": source,
                    "to": target,
                    "arrows": "to"
                } for source, target in graph["edges"]
            ]
        },
        "workspace": workspace_html,
        "memory": {
            "permanent": permanent_memory_md,
            "task": task_memory_md,
            "volatile": volatile_memory_md
        },
        "messages": messages_md
    }
    
    return json.dumps(state)