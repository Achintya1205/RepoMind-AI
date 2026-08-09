from pathlib import Path
import pickle

GRAPH_PATH = Path("graph_output/dependency_graph.pkl")


class GraphTool:

    def __init__(self):
        with open(GRAPH_PATH, "rb") as f:
            self.graph = pickle.load(f)

    def get_nodes(self, symbol):
        return [
            node
            for node in self.graph.nodes
            if node.endswith(f"::{symbol}")
        ]

    def get_node(self, symbol):
        nodes = self.get_nodes(symbol)

        if len(nodes) == 1:
            return nodes[0]

        return None

    def callers(self, symbol):
        node = self.get_node(symbol)

        if node is None:
            return []

        callers = []

        for src, dst, data in self.graph.edges(data=True):
            if dst == node and data.get("edge_type") == "CALLS":
                callers.append(src)

        return callers

    def has_call_edge(self, caller, callee):

        caller_node = self.get_node(caller)
        callee_node = self.get_node(callee)

        if not caller_node or not callee_node:
            return False

        edge = self.graph.get_edge_data(
            caller_node,
            callee_node
        )

        return edge is not None and edge.get("edge_type") == "CALLS"

    def impact(self, symbol):

        nodes = self.get_nodes(symbol)

        if not nodes:
            return []

        impacted = []
        visited = set()
        queue = list(nodes)

        while queue:

            current = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            for caller in self.graph.predecessors(current):

                edge = self.graph.get_edge_data(
                    caller,
                    current
                )

                if edge.get("edge_type") == "CALLS":

                    impacted.append(caller)
                    queue.append(caller)

        return impacted

    def callees(self, symbol):
        nodes = self.get_nodes(symbol)

        if not nodes:
            return []

        callees = []

        for node in nodes:
            for _, dst, data in self.graph.out_edges(
                node,
                data=True
            ):
                if data.get("edge_type") == "CALLS":
                    callees.append(dst)

        return callees