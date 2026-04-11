"""
Named constants to replace magic strings/numbers throughout the codebase.
Fowler: Replace Magic Number with Symbolic Constant.
"""

# Sentinel answer_text values used to mark special submission events
SENTINEL_HINT_USED = "__hint_used__"
SENTINEL_SOLUTION_REVEALED = "__solution_revealed__"

SENTINEL_ANSWERS = {SENTINEL_HINT_USED, SENTINEL_SOLUTION_REVEALED}

# Submission statuses
SUBMISSION_PASSED = "passed"
SUBMISSION_FAILED = "failed"
SUBMISSION_PENDING = "pending"

# Course statuses
COURSE_STATUS_PUBLISHED = "published"
COURSE_STATUS_PRIVATE = "private"
COURSE_STATUS_DRAFT = "draft"
COURSE_STATUS_ARCHIVED = "archived"

# Default image size limit (5 MB)
MAX_UPLOAD_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
