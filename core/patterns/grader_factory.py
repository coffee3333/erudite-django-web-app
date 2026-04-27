# Factory pattern for grading challenges.
# Instead of a long if/elif chain in the view, we look up the right
# grader key by challenge type. Adding a new challenge type
# only requires registering it here, the dispatch logic stays clean.


_REGISTRY = {
    "quiz_mcq": "quiz_mcq",
    "quiz_text": "quiz_text",
    "text": "text",
    "code": "code",
}


class GraderFactory:

    @staticmethod
    def resolve(challenge_type: str, challenge=None) -> str:
        # quiz with options uses MCQ grading; quiz without options falls back to text grading
        if challenge_type == "quiz":
            if challenge is not None and challenge.options.exists():
                return "quiz_mcq"
            return "quiz_text"
        if challenge_type not in _REGISTRY:
            raise ValueError(f"No grader registered for challenge type: {challenge_type!r}")
        return challenge_type
