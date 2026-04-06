# core/models/code_challenge.py
from django.db import models

class CodeChallengeConfig(models.Model):
    LANGUAGE_CHOICES = [
        ("python",     "Python 3"),
        ("javascript", "JavaScript (Node)"),
        ("java",       "Java"),
        ("cpp",        "C++"),
        ("sql",        "SQL"),
    ]
    challenge         = models.OneToOneField(
        "Challenge", on_delete=models.CASCADE, related_name="code_config"
    )
    language          = models.CharField(max_length=30, choices=LANGUAGE_CHOICES)
    solution_template = models.TextField(blank=True)   # starter code shown to student
    solution_hidden   = models.TextField(blank=True)   # reference solution, never exposed
    time_limit_seconds = models.PositiveIntegerField(default=5)
    memory_limit_mb    = models.PositiveIntegerField(default=128)

    def __str__(self):
        return f"Config for {self.challenge.slug} ({self.language})"


class CodeTestCase(models.Model):
    config          = models.ForeignKey(
        CodeChallengeConfig, on_delete=models.CASCADE, related_name="test_cases"
    )
    stdin           = models.TextField(blank=True)
    expected_stdout = models.TextField()
    is_public       = models.BooleanField(default=False)  # True = show as example
    weight          = models.FloatField(default=1.0)
    description     = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["id"]


class CodeSubmissionResult(models.Model):
    STATUS_CHOICES = [
        ("accepted",           "Accepted"),
        ("wrong_answer",       "Wrong Answer"),
        ("time_limit",         "Time Limit Exceeded"),
        ("memory_limit",       "Memory Limit Exceeded"),
        ("runtime_error",      "Runtime Error"),
        ("compilation_error",  "Compilation Error"),
    ]
    submission      = models.ForeignKey(
        "Submission", on_delete=models.CASCADE, related_name="test_results"
    )
    test_case       = models.ForeignKey(CodeTestCase, on_delete=models.CASCADE)
    status          = models.CharField(max_length=30, choices=STATUS_CHOICES)
    stdout          = models.TextField(blank=True)
    stderr          = models.TextField(blank=True)
    execution_time_ms = models.FloatField(null=True)
    memory_used_mb    = models.FloatField(null=True)