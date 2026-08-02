from pathlib import Path


class ImportResolver:

    def __init__(self, repo_root):

        self.repo_root = Path(repo_root)

    def extract_import_path(self, statement):

        if "from" in statement:
            return statement.split("from")[-1].strip().replace("'", "").replace('"', "").replace(";", "")

        return None

    def resolve_python_import(self, current_file, import_name):

        current_file = Path(current_file)

        possible_paths = []


        # import utils
        module_path = import_name.replace(".", "/")

        possible_paths.append(
            self.repo_root / f"{module_path}.py"
        )

        possible_paths.append(
            self.repo_root / module_path / "__init__.py"
        )


        # check relative to current file
        for path in possible_paths:

            if path.exists():

                return str(path)


        return None



    def resolve_javascript_import(self, current_file, import_path):

        current_file = Path(current_file)

        if not import_path.startswith("."):

            return None


        base_path = (
            current_file.parent /
            import_path
        )


        extensions = [
            "",
            ".js",
            ".jsx",
            ".ts",
            ".tsx"
        ]


        for ext in extensions:

            candidate = Path(
                str(base_path) + ext
            )

            if candidate.exists():

                return str(candidate)


        # index files

        for ext in extensions[1:]:

            candidate = (
                base_path /
                f"index{ext}"
            )

            if candidate.exists():

                return str(candidate)


        return None