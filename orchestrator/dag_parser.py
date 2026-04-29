import yaml

class DAGParser:
    def __init__(self, yaml_content=None):
        self.dag = {}
        if yaml_content:
            self.dag = yaml.safe_load(yaml_content)

    def load_from_file(self, file_path):
        with open(file_path, 'r') as f:
            self.dag = yaml.safe_load(f)

    def get_adjacency_list(self):
        """
        Returns {node: [children]}
        """
        adj = {}
        for node, config in self.dag.get('functions', {}).items():
            adj[node] = config.get('next', [])
        return adj

    def get_critical_path(self):
        # Simplified: just return the nodes in order for a linear chain
        # In a real DAG, we'd use topological sort and weight calculations
        nodes = list(self.dag.get('functions', {}).keys())
        return nodes
