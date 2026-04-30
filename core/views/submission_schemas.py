# core/views/submission_schemas.py
"""
Swagger/OpenAPI decorator constants for submission views.
Extracted to reduce cyclomatic complexity of submission_view.py.
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

_test_result_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "status": openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=["accepted", "wrong_answer", "time_limit", "memory_limit", "runtime_error", "compilation_error"],
            description="Result of this test case",
        ),
        "time_ms": openapi.Schema(type=openapi.TYPE_NUMBER, description="Execution time in milliseconds"),
        "stdout":  openapi.Schema(type=openapi.TYPE_STRING, description="Program output (null for hidden test cases)", nullable=True),
        "stderr":  openapi.Schema(type=openapi.TYPE_STRING, description="Error output (null for hidden test cases)", nullable=True),
    },
    required=["status", "time_ms"],
)

submit_schema = swagger_auto_schema(
    tags=["Challenge"],
    operation_summary="Submit an answer for a challenge (quiz / text / code)",
    operation_description=(
        "Behaviour depends on `challenge_type`:\n\n"
        "**quiz** — send `{ \"option_id\": <int> }`\n\n"
        "**text** — send `{ \"answer\": \"<your answer>\" }`\n\n"
        "**code** — send `{ \"code\": \"<source code>\", \"language\": \"python\" }`\n\n"
        "The `language` field is optional for code challenges — it defaults to the "
        "language configured on the challenge. Supported values: "
        "`python`, `javascript`, `java`, `cpp`.\n\n"
        "For code challenges the server executes the code against every test case "
        "in an isolated sandbox. Public test cases show their stdout/stderr in the "
        "response; hidden test cases return `null` for those fields."
    ),
    manual_parameters=[
        openapi.Parameter(
            "slug", openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge slug",
            required=True,
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="Send **one** of the three shapes depending on `challenge_type`.",
        properties={
            "option_id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="[quiz only] ID of the chosen option",
            ),
            "answer": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="[text only] Free-text answer string",
            ),
            "code": openapi.Schema(
                type=openapi.TYPE_STRING,
                description=(
                    "[code only] Full source code to execute.\n\n"
                    "**Python example:**\n"
                    "```python\n"
                    "def solution(n):\n"
                    "    return n * 2\n\n"
                    "import sys\n"
                    "print(solution(int(sys.stdin.read())))\n"
                    "```\n\n"
                    "**JavaScript example:**\n"
                    "```javascript\n"
                    "const lines = require('fs').readFileSync('/dev/stdin','utf8').trim();\n"
                    "console.log(parseInt(lines) * 2);\n"
                    "```"
                ),
            ),
            "language": openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=["python", "javascript", "java", "cpp"],
                description="[code only] Override the challenge language. Optional.",
            ),
        },
        example={
            "code": "import sys\nprint(int(sys.stdin.read().strip()) * 2)",
            "language": "python",
        },
    ),
    responses={
        200: openapi.Response(
            description=(
                "**quiz / text:** `{ correct, score }`\n\n"
                "**code:** `{ submission_id, status, score, passed, total, results[] }`"
            ),
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Shape depends on challenge_type (see above)",
            ),
            examples={
                "application/json (quiz/text)": {"correct": True, "score": 10},
                "application/json (code)": {
                    "submission_id": 42,
                    "status": "accepted",
                    "score": 30,
                    "passed": 3,
                    "total": 3,
                    "results": [
                        {"status": "accepted",     "time_ms": 12.4, "stdout": "4",  "stderr": ""},
                        {"status": "accepted",     "time_ms": 9.1,  "stdout": None, "stderr": None},
                        {"status": "wrong_answer", "time_ms": 8.7,  "stdout": None, "stderr": None},
                    ],
                },
            },
        ),
        400: openapi.Response(description="Missing required field for the challenge type"),
        401: openapi.Response(description="Not authenticated"),
        404: openapi.Response(description="Challenge / option / correct answer not found"),
    },
)

reveal_schema = swagger_auto_schema(
    tags=["Challenge"],
    operation_summary="Reveal the solution explanation for a challenge",
    operation_description=(
        "Returns the teacher's solution explanation text for the given challenge.\n\n"
        "**Important side-effects:**\n"
        "- If the student has **not yet passed** the challenge, a sentinel `Submission` record "
        "is created with `answer_text='__solution_revealed__'`. This permanently blocks "
        "future submissions for this challenge.\n"
        "- If the student has already passed, the explanation is returned without any side-effects.\n\n"
        "**Idempotent** — calling again after the reveal just returns the explanation again "
        "without creating additional records.\n\n"
        "Returns `403` if the challenge has no solution explanation configured."
    ),
    manual_parameters=[
        openapi.Parameter(
            "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
            description="Challenge slug", required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="Solution explanation text",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "solution_explanation": openapi.Schema(type=openapi.TYPE_STRING),
                },
                example={"solution_explanation": "Use a hash map to track seen values. Time complexity: O(n)."},
            ),
        ),
        401: openapi.Response(description="Not authenticated"),
        403: openapi.Response(description="No solution explanation configured for this challenge"),
        404: openapi.Response(description="Challenge not found"),
    },
)

hint_schema = swagger_auto_schema(
    tags=["Challenge"],
    operation_summary="Use the hint for a challenge (50% score penalty)",
    operation_description=(
        "Returns the hint text for a challenge and marks the student as having used it.\n\n"
        "**Score penalty:** any subsequent correct submission for this challenge will earn "
        "**50% of the normal points** (`round(points * 0.5)`).\n\n"
        "**Idempotent** — calling again just returns the hint again without creating "
        "additional records or changing the penalty.\n\n"
        "A sentinel `Submission` record with `answer_text='__hint_used__'` is created on first use. "
        "This record is excluded from all stats and status queries.\n\n"
        "Returns `403` if the challenge has no hint configured."
    ),
    manual_parameters=[
        openapi.Parameter(
            "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
            description="Challenge slug", required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="Hint text",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "hint": openapi.Schema(type=openapi.TYPE_STRING),
                },
                example={"hint": "Think about which data structure gives O(1) average lookup."},
            ),
        ),
        401: openapi.Response(description="Not authenticated"),
        403: openapi.Response(description="No hint configured for this challenge"),
        404: openapi.Response(description="Challenge not found"),
    },
)
