import json
from pathlib import Path


JAVASCRIPT_INPUT_PATH = Path(
    "ingestion/parsers/output/javascript_ast_output.json"
)

PYTHON_INPUT_PATH = Path(
    "ingestion/parsers/output/python_ast_output.json"
)

OUTPUT_PATH = Path(
    "ingestion/chunker/chunks.json"
)


def create_chunk(file_path, entity_type, entity):

    content = f"""
File: {file_path}

Lines: {entity.get("start_line")}-{entity.get("end_line")}

Type: {entity_type}

Name: {entity["name"]}

Code:

{entity["code"]}
"""


    return {
        "content": content.strip(),

        "metadata": {
            "file": file_path,
            "type": entity_type,
            "name": entity["name"],
            "start_line": entity.get("start_line"),
            "end_line": entity.get("end_line")
        }
    }

def generate_chunks(ast_data):

    chunks = []

    seen = set()


    for file_data in ast_data:

        file_path = file_data["file"]


        entities = []


        entities.extend(
            [
                ("function", f)
                for f in file_data.get("functions", [])
            ]
        )


        entities.extend(
            [
                ("arrow_function", f)
                for f in file_data.get("arrow_functions", [])
            ]
        )


        entities.extend(
            [
                ("class", c)
                for c in file_data.get("classes", [])
            ]
        )


        for entity_type, entity in entities:


            key = (
                file_path,
                entity.get("name"),
                entity.get("start_line"),
                entity.get("end_line")
            )


            if key in seen:
                continue


            seen.add(key)


            chunks.append(
                create_chunk(
                    file_path,
                    entity_type,
                    entity
                )
            )


    return chunks

def load_ast_data():

    all_data = []

    for path in (JAVASCRIPT_INPUT_PATH, PYTHON_INPUT_PATH):

        if not path.exists():
            print(f"Skipping missing {path}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            all_data.extend(json.load(f))

    return all_data


def main():

    ast_data = load_ast_data()

    chunks = generate_chunks(ast_data)


    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            chunks,
            f,
            indent=4
        )


    print(
        f"Created {len(chunks)} chunks"
    )



if __name__ == "__main__":
    main()