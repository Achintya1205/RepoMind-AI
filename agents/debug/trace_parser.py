import re
class TraceParser:

    def parse(self, trace):

        result = {
            "file": None,
            "line": None,
            "function": None
        }

        python_match = re.search(
            r'File "(.+)", line (\d+), in (\w+)',
            trace
        )


        if python_match:

            result["file"] = python_match.group(1)
            result["line"] = int(python_match.group(2))
            result["function"] = python_match.group(3)

            return result

        js_match = re.search(
            r'at (.+) \((.+):(\d+):(\d+)\)',
            trace
        )

        if js_match:

            result["function"] = js_match.group(1).split(".")[-1]
            result["file"] = js_match.group(2)
            result["line"] = int(js_match.group(3))

            return result

        js_match_no_column = re.search(
            r'at (.+) \((.+):(\d+)\)',
            trace
        )

        if js_match_no_column:

            result["function"] = js_match_no_column.group(1).split(".")[-1]
            result["file"] = js_match_no_column.group(2)
            result["line"] = int(js_match_no_column.group(3))


        return result