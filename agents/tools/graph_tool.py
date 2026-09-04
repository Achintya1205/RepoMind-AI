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
        nodes = self.get_nodes(symbol)

        if not nodes:
            return []

        node_set = set(nodes)

        callers = []

        for src, dst, data in self.graph.edges(data=True):
            if dst in node_set and data.get("edge_type") == "CALLS":
                callers.append(src)

        return callers

    def has_call_edge(self, caller, callee):

        caller_nodes = self.get_nodes(caller)
        callee_nodes = self.get_nodes(callee)

        if not caller_nodes or not callee_nodes:
            return False

        for caller_node in caller_nodes:
            for callee_node in callee_nodes:

                edge = self.graph.get_edge_data(
                    caller_node,
                    callee_node
                )

                if edge is not None and edge.get("edge_type") == "CALLS":
                    return True

        return False

    def impact(self, symbol):

        nodes = self.get_nodes(symbol)

        if not nodes:
            return []

        impacted = []
        visited = set(nodes)
        queue = list(nodes)

        while queue:

            current = queue.pop(0)

            for caller in self.graph.predecessors(current):

                if caller in visited:
                    continue

                edge = self.graph.get_edge_data(
                    caller,
                    current
                )

                if edge.get("edge_type") == "CALLS":

                    visited.add(caller)
                    impacted.append(caller)
                    queue.append(caller)

        return impacted

    def impact_with_depth(self, symbol):

        nodes = self.get_nodes(symbol)

        if not nodes:
            return []

        tagged = []
        visited = set(nodes)
        queue = [(node, 0) for node in nodes]

        while queue:

            current, depth = queue.pop(0)

            for caller in self.graph.predecessors(current):

                if caller in visited:
                    continue

                edge = self.graph.get_edge_data(
                    caller,
                    current
                )

                if edge.get("edge_type") == "CALLS":

                    visited.add(caller)
                    tagged.append((caller, depth + 1))
                    queue.append((caller, depth + 1))

        return tagged

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