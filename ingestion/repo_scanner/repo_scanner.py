from pathlib import Path


IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv"
}


IGNORE_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml"
}


LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript"
}


def detect_language(file_path):

    extension = file_path.suffix.lower()

    return LANGUAGE_MAP.get(extension)


def should_ignore(path):

    # Ignore directories
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True

    # Ignore specific files
    if path.name in IGNORE_FILES:
        return True

    return False



def scan_repository(repo_path):

    repo_path = Path(repo_path)

    files = []


    for file in repo_path.rglob("*"):

        if file.is_file():

            if should_ignore(file):
                continue


            language = detect_language(file)


            if language:

                files.append(
                    {
                        "path": str(file),
                        "language": language
                    }
                )


    return files



if __name__ == "__main__":

    repo = "sample_repos/full-stack-fastapi-template"
    results = scan_repository(repo)


    print(f"Found {len(results)} files\n")


    for file in results[:20]:

        print(
            file["path"],
            "---->",
            file["language"]
        )