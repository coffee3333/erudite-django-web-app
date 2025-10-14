from django.urls import path
from core.views.course_view import CourseUpdateAPIView, CourseCreateView

urlpatterns = [
    path('courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('courses/<slug:slug>/update/', CourseUpdateAPIView.as_view(), name='course-update'),
]

