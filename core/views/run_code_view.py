# core/views/run_code_view.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsEmailVerified
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.execution.executor import run_code_challenge
from core.models.challenge_model import Challenge


class RunCodeView(APIView):
    """
    Dry-run: execute code against PUBLIC test cases only.
    Does NOT create a Submission record.
    The student uses this to iterate and fix their code before calling /submit/.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]
    parser_classes = [parsers.JSONParser]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Run code against public test cases (no submission saved)",
        operation_description=(
            "Executes the submitted code against **only the public test cases** of a code challenge. "
            "No `Submission` record is created — this is a safe scratch-pad for the student to "
            "iterate and debug before making a final submission.\n\n"
            "Only valid for `challenge_type = 'code'`.\n\n"
            "**Tip for writing code:** your program must read input from `stdin` and write output to "
            "`stdout`. The server pipes the test case `stdin` value into your process and compares "
            "your `stdout` (stripped of leading/trailing whitespace) to `expected_stdout`.\n\n"
            "**Python example** (reads one integer, prints it doubled):\n"
            "```python\n"
            "import sys\n"
            "n = int(sys.stdin.read().strip())\n"
            "print(n * 2)\n"
            "```\n\n"
            "**JavaScript example:**\n"
            "```javascript\n"
            "const n = parseInt(require('fs').readFileSync('/dev/stdin', 'utf8').trim());\n"
            "console.log(n * 2);\n"
            "```"
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
            required=["code"],
            properties={
                "code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Full source code to execute",
                ),
                "language": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["python", "javascript", "java", "cpp"],
                    description="Override the challenge's configured language. Optional.",
                ),
            },
            example={
                "code": "import sys\nprint(int(sys.stdin.read().strip()) * 2)",
                "language": "python",
            },
        ),
        responses={
            200: openapi.Response(
                description="Execution results for all public test cases",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "run_only": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Always true — indicates this was a dry-run, not a graded submission",
                        ),
                        "passed":  openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of public tests passed"),
                        "total":   openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of public tests"),
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Test case label set by the teacher"),
                                    "stdin":        openapi.Schema(type=openapi.TYPE_STRING, description="Input that was fed to your program"),
                                    "expected":     openapi.Schema(type=openapi.TYPE_STRING, description="Expected output"),
                                    "got":          openapi.Schema(type=openapi.TYPE_STRING, description="Your program's actual output"),
                                    "status":       openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        enum=["accepted", "wrong_answer", "time_limit", "memory_limit", "runtime_error", "compilation_error"],
                                    ),
                                    "time_ms": openapi.Schema(type=openapi.TYPE_NUMBER),
                                    "stderr":  openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                },
                            ),
                        ),
                    },
                    example={
                        "run_only": True,
                        "passed": 1,
                        "total": 1,
                        "results": [
                            {
                                "description": "Basic case",
                                "stdin": "4",
                                "expected": "8",
                                "got": "8",
                                "status": "accepted",
                                "time_ms": 31.2,
                                "stderr": "",
                            }
                        ],
                    },
                ),
            ),
            400: openapi.Response(description="Missing 'code' field or not a code challenge"),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="Email not verified"),
            404: openapi.Response(description="Challenge not found or no public test cases configured"),
        },
    )
    def post(self, request, slug):
        challenge = get_object_or_404(
            Challenge.objects.select_related("code_config"),
            slug=slug,
        )

        if challenge.challenge_type != "code":
            return Response(
                {"detail": "This endpoint is only for code challenges."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = request.data.get("code", "").strip()
        if not code:
            return Response(
                {"detail": "Field 'code' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = getattr(challenge, "code_config", None)
        if config is None:
            return Response(
                {"detail": "Code config not set for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only public test cases — student can see all input/output details
        public_test_cases = list(config.test_cases.filter(is_public=True))
        if not public_test_cases:
            return Response(
                {"detail": "No public test cases configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        language = request.data.get("language", config.language)

        results = run_code_challenge(
            code,
            language,
            public_test_cases,
            time_limit_s=config.time_limit_seconds,
            memory_mb=config.memory_limit_mb,
        )

        passed = sum(1 for r in results if r.status == "accepted")

        return Response({
            "run_only": True,
            "passed": passed,
            "total": len(results),
            "results": [
                {
                    "description": next(
                        tc.description for tc in public_test_cases if tc.id == r.test_case_id
                    ),
                    "stdin":    next(
                        tc.stdin for tc in public_test_cases if tc.id == r.test_case_id
                    ),
                    "expected": next(
                        tc.expected_stdout for tc in public_test_cases if tc.id == r.test_case_id
                    ),
                    "got":      r.stdout,
                    "status":   r.status,
                    "time_ms":  r.time_ms,
                    "stderr":   r.stderr or None,
                }
                for r in results
            ],
        }, status=status.HTTP_200_OK)
