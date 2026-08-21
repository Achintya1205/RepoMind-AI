def format_sources(chunks):

    if not chunks:
        return "No relevant source code was found."

    blocks = []

    for i, item in enumerate(chunks, start=1):

        meta = item["metadata"]
        content = item.get("chunk", item.get("content", ""))

        header = (
            f"[S{i}] file: {meta.get('file')} "
            f"lines: {meta.get('start_line')}-{meta.get('end_line')} "
            f"type: {meta.get('type')} name: {meta.get('name')}"
        )

        blocks.append(f"{header}\n{content}")

    return "\n\n---\n\n".join(blocks)