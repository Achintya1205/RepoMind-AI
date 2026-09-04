def extract_symbol(query, graph_tool):
    """
    Find the known function/class name (from the dependency graph) that
    appears in the query. Matches against real symbols instead of a regex
    guess, and prefers the longest match so a short name (e.g. "User")
    doesn't win over a more specific one (e.g. "UserCard") when both
    appear in the query.

    Returns None if no known symbol is mentioned - callers should treat
    that as "couldn't identify a target," not silently fall back to a
    default symbol.
    """

    import re

    query_lower = query.lower()

    names = set()

    for _, data in graph_tool.graph.nodes(data=True):

        name = data.get("name")

        if name:
            names.add(name)

    candidates = sorted(names, key=len, reverse=True)

    for name in candidates:
        
        if re.search(r'\b' + re.escape(name.lower()) + r'\b', query_lower):
            return name

    return None