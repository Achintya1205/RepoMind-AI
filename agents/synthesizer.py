class Synthesizer:

    def format(self, state):

        if state["verified"]["passed"]:

            return {
                "answer": state["answer"],
                "citations": state.get("metadata", [])
            }

        return {
            "answer": "Unable to verify answer",
            "reasons": state["verified"]["reasons"]
        }
