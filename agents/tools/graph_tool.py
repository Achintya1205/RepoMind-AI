from pathlib import Path
import pickle


GRAPH_PATH = Path("graph_output/dependency_graph.pkl")


class GraphTool:

    def __init__(self):
        with open(GRAPH_PATH, "rb") as f:
            self.graph = pickle.load(f)

    def get_node(self, symbol):
        for node in self.graph.nodes:
            if node.endswith(f"::{symbol}"):
                return node
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


        return self.graph.has_edge(
            caller_node,
            callee_node
        )

    def impact(self, symbol):

        node = self.get_node(symbol)

        if node is None:
            return []

        impacted = []
        visited = set()
        queue = [node]

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
        node = self.get_node(symbol)

        if node is None:
            return []

        callees = []

        for src, dst, data in self.graph.edges(data=True):
            if src == node and data.get("edge_type") == "CALLS":
                callees.append(dst)

        return callees

    