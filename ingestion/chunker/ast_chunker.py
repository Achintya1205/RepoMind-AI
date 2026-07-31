import json
from pathlib import Path


INPUT_PATH = Path(
    "ingestion/parsers/output/javascript_ast_output.json"
)

OUTPUT_PATH = Path(
    "ingestion/chunker/chunks.json"
)


def create_chunk(file_path, entity_type, entity):

    content = f"""
File: {file_path}

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
            "name": entity["name"]
        }
    }

def generate_chunks(ast_data):

    chunks = []


    for file_data in ast_data:

        file_path = file_data["file"]


        # functions

        for function in file_data.get("functions", []):

            chunks.append(
                create_chunk(
                    file_path,
                    "function",
                    function
                )
            )

        for function in file_data.get("arrow_functions", []):

            chunks.append(
                create_chunk(
                    file_path,
                    "arrow_function",
                    function
                )
            )

        for cls in file_data.get("classes", []):

            chunks.append(
                create_chunk(
                    file_path,
                    "class",
                    cls
                )
            )


    return chunks



def main():

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        ast_data = json.load(f)


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