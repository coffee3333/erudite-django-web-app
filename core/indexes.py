"""
Database index definitions for performance-critical models.
Applied via Meta.indexes on models with frequent JOIN/filter operations.
"""

# This module documents the index strategy applied to models:
#
# CourseEnrollment (core/models/enrollment_model.py):
#   - Index on (course_id, student_id) — enrollment check is the hottest query
#   - Index on student_id alone — dashboard "courses touched" query
#
# CourseFeedback (core/models/feedback_model.py):
#   - Index on course_id — list all feedback for a course
#   - Index on (course_id, user_id) — unique_together, auto-indexed by Django
#
# CourseBookmark (core/models/bookmark_model.py):
#   - Index on user_id — "get my bookmarked courses" query
#   - Index on (course_id, user_id) — unique_together, auto-indexed by Django
#
# Submission (core/models/submission_model.py):
#   - Index on (user_id, challenge_id) — user_status query in ChallengeListSerializer
#   - Index on (user_id, status) — dashboard total_points computation
#
# These indexes are declared via Meta.indexes = [...] in each model's Meta class.
