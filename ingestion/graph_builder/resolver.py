from pathlib import Path


class ImportResolver:

    def __init__(self, repo_root):

        self.repo_root = Path(repo_root)


    def extract_import_path(self, statement):

        if "from" in statement:

            return (
                statement
                .split("from")[-1]
                .strip()
                .replace("'", "")
                .replace('"', "")
                .replace(";", "")
            )

        return None


    def resolve_python_import(self, current_file, import_name):

        current_file = Path(current_file)

        possible_paths = []

        module_path = import_name.replace(".", "/")

        possible_paths.append(
            self.repo_root / f"{module_path}.py"
        )

        possible_paths.append(
            self.repo_root / module_path / "__init__.py"
        )


        for path in possible_paths:

            if path.exists():

                return str(path)


        return None



    def resolve_javascript_import(self, current_file, import_path):

        current_file = Path(current_file)


        # ----------------------------
        # Relative imports
        # ./file
        # ../file
        # ----------------------------

        if import_path.startswith("."):

            base_path = (
                current_file.parent /
                import_path
            )


        # ----------------------------
        # Alias imports
        # @/ -> app/src/
        # Example:
        # @/lib/authorization
        # ----------------------------

        elif import_path.startswith("@/"):

            relative = import_path.replace("@/", "")


            parts = current_file.parts

            app_name = None


            if "apps" in parts:

                index = parts.index("apps")

                app_name = parts[index + 1]


            if app_name is None:

                return None


            base_path = (
                self.repo_root
                / "apps"
                / app_name
                / "src"
                / relative
            )


        else:

            return None



        extensions = [
            "",
            ".js",
            ".jsx",
            ".ts",
            ".tsx"
        ]


        # direct file match

        for ext in extensions:

            candidate = Path(
                str(base_path) + ext
            )

            if candidate.exists():

                return str(candidate)



        # index file match

        for ext in extensions[1:]:

            candidate = (
                base_path /
                f"index{ext}"
            )

            if candidate.exists():

                return str(candidate)


        return None