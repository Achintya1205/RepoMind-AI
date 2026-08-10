import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from python_parser import PythonParser


PROJECT_ROOT = Path(__file__).parent.parent.parent

REPO_PATH = PROJECT_ROOT / "sample_repos" / "full-stack-fastapi-template"

OUTPUT_PATH = PROJECT_ROOT / "ingestion" / "parsers" / "output" / "python_ast_output.json"


def collect_python_files(repo_path):

    python_files = []

    for file in repo_path.rglob("*.py"):
        python_files.append(file)

    return python_files


def main():

    parser = PythonParser()

    results = []

    python_files = collect_python_files(REPO_PATH)

    print(f"Found {len(python_files)} Python files")

    for file in python_files:

        try:
            result = parser.process_file(file)
            result["file"] = str(file.relative_to(PROJECT_ROOT))
            results.append(result)

        except Exception as e:
            print(f"Failed: {file}")
            print(e)


    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=4
        )


    print(f"Saved output to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()