from pathlib import Path


class ImportResolver:

    def __init__(self, repo_root):

        self.repo_root = Path(repo_root).resolve()


    def _infer_repo_root(self, current_file):

        parts = current_file.parts

        if "sample_repos" in parts:

            index = parts.index("sample_repos")

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

        current_file = Path(current_file).resolve()

        if import_name.startswith("."):
            return self._resolve_relative_python_import(
                current_file, import_name
            )

        module_path = import_name.replace(".", "/")

        repo_boundary = self._infer_repo_root(current_file)

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


    def _resolve_relative_python_import(self, current_file, import_name):

        stripped = import_name.lstrip(".")

        dot_count = len(import_name) - len(stripped)

        base_dir = current_file.parent

        for _ in range(dot_count - 1):
            base_dir = base_dir.parent

        if not stripped:
            candidate = base_dir / "__init__.py"

            if candidate.exists():
                return str(candidate)

            return None

        module_path = stripped.replace(".", "/")

        for candidate in (
            base_dir / f"{module_path}.py",
            base_dir / module_path / "__init__.py"
        ):

            if candidate.exists():
                return str(candidate)

        return None



    def resolve_javascript_import(self, current_file, import_path):

        current_file = Path(current_file).resolve()


        if import_path.startswith("."):

            base_path = (
                current_file.parent /
                import_path
            )

        elif import_path.startswith("@/"):

            relative = import_path.replace("@/", "")

            parts = current_file.parts

            repo_root = self._infer_repo_root(current_file)

            candidate_bases = []

            if "apps" in parts:

                index = parts.index("apps")
                app_name = parts[index + 1]

                candidate_bases.append(
                    repo_root / "apps" / app_name / "src" / relative
                )

            candidate_bases.append(repo_root / "src" / relative)

            candidate_bases.append(repo_root / relative)

            for base_path in candidate_bases:

                resolved = self._resolve_with_extensions(base_path)

                if resolved:
                    return resolved

            return None


        else:

            return None


        return self._resolve_with_extensions(base_path)

    def _resolve_with_extensions(self, base_path):

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