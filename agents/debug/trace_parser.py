import re


class TraceParser:


    def parse(self, trace):

        result = {
            "file": None,
            "line": None,
            "function": None
        }


        # Python:
        # File "app.py", line 20, in login
        python_match = re.search(
            r'File "(.+)", line (\d+), in (\w+)',
            trace
        )


        if python_match:

            result["file"] = python_match.group(1)
            result["line"] = int(python_match.group(2))
            result["function"] = python_match.group(3)

            return result


        # Javascript:
        # at login (src/auth.js:20:5)
        js_match = re.search(
            r'at (.+) \((.+):(\d+):\d+\)',
            trace
        )


        if js_match:

            result["function"] = js_match.group(1)
            result["file"] = js_match.group(2)
            result["line"] = int(js_match.group(3))


        return result