from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.models.course_model import Course
from core.models.certificate_model import Certificate
from core.patterns.certificate_builder import CertificateBuilder


class CourseCertificateView(APIView):
    """
    Returns the certificate metadata for a course the user has completed.
    A certificate is issued automatically when the student's pass rate meets
    the course's completion_threshold (default 80%). Includes a pdf_download_url.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Certificate"],
        operation_summary="Get certificate metadata for a course",
        operation_description=(
            "Returns the certificate the authenticated user has earned for this course.\n\n"
            "A certificate is issued automatically when the user passes enough challenges to "
            "meet the course's `completion_threshold` (default 80%).\n\n"
            "Includes a `pdf_download_url` pointing to the PDF download endpoint."
        ),
        manual_parameters=[
            openapi.Parameter("slug", openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, description="Course slug"),
        ],
        responses={
            200: openapi.Response(
                description="Certificate metadata",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "certificate_id":    openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                        "issued_at":         openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                        "score_pct":         openapi.Schema(type=openapi.TYPE_NUMBER, description="Score percentage at time of issue"),
                        "pdf_download_url":  openapi.Schema(type=openapi.TYPE_STRING, description="URL to download the PDF certificate"),
                    },
                    example={
                        "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
                        "issued_at": "2025-04-01T12:00:00Z",
                        "score_pct": 90.0,
                        "pdf_download_url": "https://example.com/platform/courses/my-course/certificate/download/",
                    },
                ),
            ),
            401: openapi.Response(description="Not authenticated"),
            404: openapi.Response(description="Course not found, or certificate not yet earned"),
        },
    )
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, status__in=["published", "private"])
        cert = Certificate.objects.filter(user=request.user, course=course).select_related("course").first()
        if not cert:
            return Response({"detail": "Certificate not yet earned."}, status=404)
        return Response({
            "certificate_id": str(cert.certificate_id),
            "issued_at": cert.issued_at,
            "score_pct": cert.score_pct,
            "pdf_download_url": request.build_absolute_uri(f"download/"),
        })


class CourseCertificateDownloadView(APIView):
    """
    Generates and streams the certificate as a PDF file.
    Returns application/pdf with Content-Disposition: attachment.
    Returns 404 if the certificate has not been earned yet.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Certificate"],
        operation_summary="Download certificate as PDF",
        operation_description=(
            "Generates and streams a PDF certificate for the authenticated user.\n\n"
            "The response is an `application/pdf` file download with the filename "
            "`certificate_<uuid>.pdf`.\n\n"
            "Returns 404 if the certificate has not been earned yet."
        ),
        manual_parameters=[
            openapi.Parameter("slug", openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, description="Course slug"),
        ],
        responses={
            200: openapi.Response(description="PDF file stream (application/pdf)"),
            401: openapi.Response(description="Not authenticated"),
            404: openapi.Response(description="Course not found, or certificate not yet earned"),
        },
    )
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, status__in=["published", "private"])
        cert = Certificate.objects.filter(user=request.user, course=course).select_related("user", "course").first()
        if not cert:
            return Response({"detail": "Certificate not yet earned."}, status=404)

        pdf_bytes = (
            CertificateBuilder()
            .set_recipient(cert.user)
            .set_course(cert.course)
            .set_certificate_id(cert.certificate_id)
            .set_issued_at(cert.issued_at)
            .set_score(cert.score_pct)
            .build()
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="certificate_{cert.certificate_id}.pdf"'
        return response
