from pathlib import Path


class ImportResolver:

    def __init__(self, repo_root):

        self.repo_root = Path(repo_root)


    def _infer_repo_root(self, current_file):

        parts = current_file.parts

        if "sample_repos" in parts:

            index = parts.index("sample_repos")

            # sample_repos/<repo-name>
            return Path(*parts[:index + 2])

        return self.repo_root

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

        module_path = import_name.replace(".", "/")

        repo_boundary = self._infer_repo_root(current_file)

        # Try every ancestor directory between the importing file and the
        # sample repo's own root as a candidate package root - handles
        # any layout (backend/app/, src/app/, app/ directly, etc.)
        # without hardcoding a specific subfolder name.
        candidate_root = current_file.parent

        candidates = [candidate_root]

        while candidate_root != repo_boundary and repo_boundary in candidate_root.parents:
            candidate_root = candidate_root.parent
            candidates.append(candidate_root)

        if repo_boundary not in candidates:
            candidates.append(repo_boundary)

        for root in candidates:

            for candidate in (
                root / f"{module_path}.py",
                root / module_path / "__init__.py"
            ):

                if candidate.exists():
                    return str(candidate)

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
                self._infer_repo_root(current_file)
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