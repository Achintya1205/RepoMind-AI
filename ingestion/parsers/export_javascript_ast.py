import json
from pathlib import Path

from javascript_parser import JavascriptParser

REPO_PATH = Path("sample_repos/bulletproof-react")

OUTPUT_PATH = Path(
    "ingestion/parsers/output/javascript_ast_output.json"
)


def collect_javascript_files(repo_path):

    files = []

    patterns = ["*.js", "*.jsx", "*.ts", "*.tsx"]

    for pattern in patterns:
        files.extend(repo_path.rglob(pattern))

    return files


def main():

    parser = JavascriptParser()

    results = []

    javascript_files = collect_javascript_files(REPO_PATH)

    print(f"Found {len(javascript_files)} JavaScript/TypeScript files")

    for file in javascript_files:

        try:
            result = parser.process_file(file)
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