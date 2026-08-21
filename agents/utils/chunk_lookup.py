import json
from pathlib import Path


CHUNKS_PATH = Path(
    "ingestion/chunker/chunks.json"
)


class ChunkStore:

    def __init__(self, path=CHUNKS_PATH):

        with open(path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

    def get_by_name(self, name, limit=1):

        if not name:
            return []

        name_lower = name.lower()

        matches = [
            chunk
            for chunk in self.chunks
            if chunk["metadata"].get("name", "").lower() == name_lower
        ]

        return matches[:limit]

    def get_by_file(self, file_path, limit=3):

        if not file_path:
            return []

        matches = [
            chunk
            for chunk in self.chunks
            if chunk["metadata"].get("file") == file_path
        ]

        return matches[:limit]

    def get_for_names(self, names, total_limit=4):

        seen = set()
        results = []

        for name in names:

            short_name = name.split("::")[-1] if "::" in name else name

            if short_name in seen:
                continue

            seen.add(short_name)

            results.extend(self.get_by_name(short_name, limit=1))

            if len(results) >= total_limit:
                break

        return results[:total_limit]

    def get_for_files(self, file_paths, per_file_limit=2, total_limit=6):

        results = []

        for path in file_paths:

            results.extend(self.get_by_file(path, limit=per_file_limit))

            if len(results) >= total_limit:
                break

        return results[:total_limit]