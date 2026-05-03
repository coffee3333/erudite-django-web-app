from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models.course_model import Course
from core.models.enrollment_model import CourseEnrollment
from core.models.feedback_model import CourseFeedback
from core.serializers.feedback_serializer import CourseFeedbackSerializer
from core.utils.access import user_can_access_course


def _get_course(slug):
    return generics.get_object_or_404(Course, slug=slug)


def _can_submit_feedback(user, course):
    """Anyone who can access the course may review it, except the owner.
    - Published course: any authenticated non-owner user.
    - Private course: must be enrolled.
    """
    if course.owner == user:
        return False
    if user.is_staff:
        return True
    if course.status == "published":
        return True
    return CourseEnrollment.objects.filter(course=course, student=user).exists()


class CourseFeedbackListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        course = _get_course(slug)
        if not user_can_access_course(request.user, course):
            raise PermissionDenied("You do not have access to this course's reviews.")
        qs = CourseFeedback.objects.filter(course=course).select_related("user").order_by("-created_at")
        serializer = CourseFeedbackSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, slug):
        return CourseFeedbackCreateView().post(request, slug)


class CourseFeedbackCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        course = _get_course(slug)
        if not _can_submit_feedback(request.user, course):
            raise PermissionDenied("You must be enrolled in this course to leave a review.")
        if CourseFeedback.objects.filter(course=course, user=request.user).exists():
            raise ValidationError("You have already reviewed this course. Edit your existing review instead.")
        serializer = CourseFeedbackSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseFeedbackUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, slug):
        course = _get_course(slug)
        feedback = generics.get_object_or_404(CourseFeedback, course=course, user=request.user)
        serializer = CourseFeedbackSerializer(feedback, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CourseFeedbackDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, slug):
        course = _get_course(slug)
        feedback = generics.get_object_or_404(CourseFeedback, course=course, user=request.user)
        feedback.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
