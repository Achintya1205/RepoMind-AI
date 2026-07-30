from resolver import ImportResolver


resolver = ImportResolver(
    "sample_repos/bulletproof-react"
)


result = resolver.resolve_javascript_import(
    "sample_repos/bulletproof-react/src/App.jsx",
    "./components/Button"
)


print(result)