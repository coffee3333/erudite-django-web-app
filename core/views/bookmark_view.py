from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models.bookmark_model import CourseBookmark
from core.models.course_model import Course
from core.serializers.course_serializer import CourseListSerializer


class CourseBookmarkToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        course = generics.get_object_or_404(Course, slug=slug)
        bookmark = CourseBookmark.objects.filter(course=course, user=request.user).first()
        if bookmark:
            bookmark.delete()
            return Response({"bookmarked": False})
        CourseBookmark.objects.create(course=course, user=request.user)
        return Response({"bookmarked": True})


class BookmarkedCoursesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseListSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Course.objects.filter(
            bookmarks__user=self.request.user
        ).order_by("-bookmarks__created_at")
