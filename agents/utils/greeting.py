import re


GREETING_PHRASES = {
    "hi", "hello", "hey", "yo", "sup", "howdy", "greetings",
    "hi there", "hello there", "hey there",
    "good morning", "good afternoon", "good evening",
    "whats up", "how are you", "hows it going",
    "test", "testing"
}


def is_greeting(query):
    """
    True only if the ENTIRE message (after stripping punctuation) is a
    known greeting/small-talk phrase - deliberately conservative, so a
    real short question that happens to start with "hi" (e.g. "hi, how
    does auth work?") is never misclassified and skipped.
    """

    cleaned = re.sub(r"[^\w\s']", "", query.strip().lower())

    return cleaned in GREETING_PHRASES