class VerificationRetry:

    def __init__(self, verifier, max_retries=2):
        self.verifier = verifier
        self.max_retries = max_retries


    def run(self, answer):

        for attempt in range(self.max_retries + 1):

            result = self.verifier.verify(answer)

            if result["passed"]:
                return result

            print(
                f"Retry {attempt + 1}:",
                result["reasons"]
            )


        return result