from rest_framework import generics, permissions, status, parsers
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from core.models.course_model import Course
from core.permissions import IsAuthorOrReadOnly, IsTeacherUser, IsEmailVerified
from core.serializers.course_serializer import (CourseUpdateSerializer, CourseCreateSerializer)

class CourseCreateView(generics.CreateAPIView):
    """
    Create a new course.
    Only authenticated users can create courses.
    """
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsEmailVerified]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    swagger_schema_fields = {"tags": ["Courses"]}

    @swagger_auto_schema(
        operation_description="Create a new course.",
        tags=["Courses"],
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description="Title of the course", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('description', openapi.IN_FORM, description="Description of the course", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('language', openapi.IN_FORM, description="Language of the course", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('level', openapi.IN_FORM, description="Level of the course", type=openapi.TYPE_STRING,
                              enum=['beginner', 'intermediate', 'advanced'], required=True),
            openapi.Parameter('status', openapi.IN_FORM, description="Status of the course", type=openapi.TYPE_STRING,
                              enum=['draft', 'published', 'archived'], required=True),
            openapi.Parameter('featured_image', openapi.IN_FORM, description="Featured image file upload (optional)", type=openapi.TYPE_FILE, required=False),
        ],
        responses={
            201: CourseCreateSerializer,
            400: "Bad Request: Invalid input data",
            401: "Unauthorized: Authentication required",
            500: "Internal Server Error",
        }
    )
    def post(self, request, *args, **kwargs):
        """Handle course creation with clean JSON responses."""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                course = self.perform_create(serializer)
                return Response(
                    {"slug": course.slug, "message": "Course created successfully."},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"Error creating course: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer):
        """Assign the authenticated user as the owner."""
        return serializer.save(owner=self.request.user)

class CourseUpdateAPIView(generics.UpdateAPIView):
    """
    Update a course by slug (partial or full update).
    Only the course owner or staff can modify it.
    """
    serializer_class = CourseUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    lookup_field = "slug"
    swagger_schema_fields = {"tags": ["Courses"]}

    def get_queryset(self):
        """Return only non-archived courses."""
        return Course.objects

    def get_object(self):
        """Retrieve course and check permissions."""
        slug = self.kwargs.get("slug")
        try:
            course = Course.objects.get(slug=slug)
        except Course.DoesNotExist:
            raise NotFound("Course not found.")

        self.check_object_permissions(self.request, course)
        return course

    @swagger_auto_schema(
        operation_description="Update a course by slug (full update allowed).",
        tags=["Courses"],
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_PATH, description="Slug of the course", type=openapi.TYPE_STRING),
            openapi.Parameter('title', openapi.IN_FORM, description="Title of the course", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('description', openapi.IN_FORM, description="Description of the course", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('language', openapi.IN_FORM, description="Language of the course", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('level', openapi.IN_FORM, description="Level of the course", type=openapi.TYPE_STRING,
                              enum=["beginner", "intermediate", "advanced"], required=False),
            openapi.Parameter('status', openapi.IN_FORM, description="Course status", type=openapi.TYPE_STRING,
                              enum=["draft", "published", "archived"], required=False),
            openapi.Parameter('featured_image', openapi.IN_FORM, description="Featured image file upload", type=openapi.TYPE_FILE, required=False),
        ],
        responses={
            200: CourseUpdateSerializer,
            400: "Bad Request: Invalid input data",
            401: "Unauthorized: Authentication required",
            403: "Forbidden: You can only update your own courses",
            404: "Not Found: Course does not exist"
        }
    )
    def put(self, request, *args, **kwargs):
        """Full update (PUT) — all fields allowed."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            if serializer.is_valid():
                updated_course, has_updates = serializer.save()
                if not has_updates:
                    return Response({
                        "message": "No changes detected",
                        "data": updated_course
                    }, status=status.HTTP_200_OK)
                return Response(updated_course, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": f"Error updating course: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Partially update a course (PATCH).",
        tags=["Courses"],
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_PATH, description="Slug of the course", type=openapi.TYPE_STRING),
            openapi.Parameter('title', openapi.IN_FORM, description="Title of the course", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('description', openapi.IN_FORM, description="Description of the course", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('language', openapi.IN_FORM, description="Language of the course", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('level', openapi.IN_FORM, description="Level of the course", type=openapi.TYPE_STRING,
                              enum=["beginner", "intermediate", "advanced"], required=False),
            openapi.Parameter('status', openapi.IN_FORM, description="Course status", type=openapi.TYPE_STRING,
                              enum=["draft", "published", "archived"], required=False),
            openapi.Parameter('featured_image', openapi.IN_FORM, description="Featured image file upload", type=openapi.TYPE_FILE, required=False),
        ],
        responses={
            200: CourseUpdateSerializer,
            400: "Bad Request: Invalid input data",
            401: "Unauthorized: Authentication required",
            403: "Forbidden: You can only update your own courses",
            404: "Not Found: Course does not exist"
        }
    )
    def patch(self, request, *args, **kwargs):
        """Partial update (PATCH) — only provided fields will change."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                updated_course, has_updates = serializer.save()
                if not has_updates:
                    return Response({
                        "message": "No changes detected",
                        "data": updated_course
                    }, status=status.HTTP_200_OK)
                return Response(updated_course, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": f"Error updating course: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

