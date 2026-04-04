from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, permissions, status, parsers
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from core.filters import CourseFilter
from core.models.course_model import Course
from core.models.enrollment_model import CourseEnrollment
from core.pagination import CustomPagination
from core.permissions import IsAuthorOrReadOnly, IsTeacherUser, IsEmailVerified
from core.serializers.course_serializer import (CourseListSerializer, CourseDetailSerializer,
                                                CourseUpdateSerializer, CourseCreateSerializer)

class CourseListAPIView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        qs = Course.objects.select_related("owner")
        if user.is_authenticated and user.is_staff:
            return qs
        if user.is_authenticated:
            enrolled_ids = CourseEnrollment.objects.filter(student=user).values_list("course_id", flat=True)
            return qs.filter(
                Q(status="published") |
                Q(status="private", id__in=enrolled_ids) |
                Q(owner=user, status__in=["draft", "private", "archived"])
            )
        return qs.filter(status="published")

    @swagger_auto_schema(
        operation_description="Get all published courses with filters, sorting, and pagination.",
        tags=['Courses'],
        operation_summary="List of all courses",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search via title, description or owner username", type=openapi.TYPE_STRING),
            openapi.Parameter('title', openapi.IN_QUERY, description="Filter by course title", type=openapi.TYPE_STRING),
            openapi.Parameter('owner_username', openapi.IN_QUERY, description="Filter by owner username", type=openapi.TYPE_STRING),
            openapi.Parameter('level', openapi.IN_QUERY, description="Filter by course level (beginner, intermediate, advanced)", type=openapi.TYPE_STRING),
            openapi.Parameter('sort_by', openapi.IN_QUERY, description="Sort by: newest, oldest, title_asc, title_desc", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Number of results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: CourseListSerializer(many=True),
            400: "Bad Request",
            500: "Internal Server Error"
        }
    )
    def get(self, request, *args, **kwargs):
        """Retrieve all published courses with filters, sorting, and pagination."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except (DjangoValidationError, DRFValidationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        operation_summary="Create a new course.",
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
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            course = self.perform_create(serializer)
            return Response(
                {"slug": course.slug, "message": "Course created successfully."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        """Assign the authenticated user as the owner."""
        return serializer.save(owner=self.request.user)

class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    swagger_schema_fields = {"tags": ["Courses"]}

    def get_queryset(self):
        """Define which courses the user can access."""
        user = self.request.user

        qs = (
            Course.objects
            .select_related("owner")
            .prefetch_related("topics__challenges")
        )

        if user.is_authenticated and user.is_staff:
            return qs

        if user.is_authenticated:
            enrolled_ids = CourseEnrollment.objects.filter(student=user).values_list("course_id", flat=True)
            return qs.filter(
                Q(status="published") |
                Q(status="private", id__in=enrolled_ids) |
                Q(owner=user, status__in=["draft", "private", "archived"])
            )

        # Unauthenticated users see only published courses
        return qs.filter(status="published")

    def get_object(self):
        """Ensure restricted access for drafts, archived, and private courses."""
        obj = super().get_object()
        user = self.request.user

        # Drafts: visible only to owner or staff
        if obj.status == "draft" and (
            not user.is_authenticated or (obj.owner != user and not user.is_staff)
        ):
            raise NotFound("Course not found.")

        # Archived: visible only to owner or staff
        if obj.status == "archived" and (
            not user.is_authenticated or (obj.owner != user and not user.is_staff)
        ):
            raise NotFound("Course not found.")

        # Private: visible only to owner, staff, or enrolled students
        if obj.status == "private":
            if not user.is_authenticated:
                raise NotFound("Course not found.")
            if not user.is_staff and obj.owner != user:
                if not CourseEnrollment.objects.filter(course=obj, student=user).exists():
                    raise NotFound("Course not found.")

        return obj


    @swagger_auto_schema(
        operation_description="Retrieve a course by slug with its topics and challenges.",
        tags=["Courses"],
        operation_summary="Course detail via slug",
        manual_parameters=[
            openapi.Parameter(
                "slug",
                openapi.IN_PATH,
                description="Course slug",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: CourseDetailSerializer,
            404: "Not Found",
            401: "Unauthorized",
        },
    )

    def get(self, request, *args, **kwargs):
        """Retrieve course details and return clean JSON even in DEBUG mode."""
        try:
            return super().get(request, *args, **kwargs)
        except Course.DoesNotExist:
            raise NotFound("Course not found.")

class CourseUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CourseUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    lookup_field = "slug"
    swagger_schema_fields = {"tags": ["Courses"]}

    def get_queryset(self):
        return Course.objects.all()

    def get_object(self):
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
        operation_summary="Update course by slug, full update",
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
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            if serializer.is_valid():
                updated_course, has_updates = serializer.save()
                if not has_updates:
                    return Response({"message": "No changes detected", "data": updated_course}, status=status.HTTP_200_OK)
                return Response(updated_course, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

    @swagger_auto_schema(
        operation_description="Partially update a course (PATCH).",
        tags=["Courses"],
        operation_summary="Update course by slug, partially update",
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
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                updated_course, has_updates = serializer.save()
                if not has_updates:
                    return Response({"message": "No changes detected", "data": updated_course}, status=status.HTTP_200_OK)
                return Response(updated_course, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

class CourseDeleteAPIView(generics.DestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    lookup_field = "slug"
    swagger_schema_fields = {"tags": ["Courses"]}

    def get_object(self):
        slug = self.kwargs.get("slug")
        try:
            obj = Course.objects.get(slug=slug)
        except Course.DoesNotExist:
            raise NotFound("Course not found.")

        user = self.request.user
        if not (user.is_staff or obj.owner == user):
            raise PermissionDenied("You can only delete your own courses.")
        return obj

    def perform_destroy(self, instance):
        instance.delete()

    @swagger_auto_schema(
        operation_description="Delete a course by slug. This will also remove all related topics and challenges.",
        tags=["Courses"],
        operation_summary="Delete course by slug",
        manual_parameters=[
            openapi.Parameter(
                "slug",
                openapi.IN_PATH,
                description="Course slug",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            204: "Course and all related data deleted.",
            401: "Unauthorized: Authentication required.",
            403: "Forbidden: You can only delete your own courses.",
            404: "Not Found: Course not found.",
        },
    )
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)