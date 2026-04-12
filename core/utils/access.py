from core.models.enrollment_model import CourseEnrollment


def user_can_access_course(user, course):
    """Return True if user may view content inside the given course."""
    if not user or not user.is_authenticated:
        return course.status == "published"
    if user.is_staff:
        return True
    if course.owner == user:
        return True
    if course.status == "published":
        return True
    if course.status == "private":
        return CourseEnrollment.objects.filter(course=course, student=user).exists()
    # draft / archived — owner + staff only (already handled above)
    return False
