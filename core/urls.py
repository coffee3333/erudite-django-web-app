from django.urls import path

from core.views.challenge_view import ChallengeCreateAPIView, ChallengeListAPIView, ChallengeCreateView, UseHintView, RevealSolutionView, ChallengeUpdateAPIView, ChallengeDeleteAPIView
from core.views.challenge_check_view import ChallengeAnswerCheckAPIView
from core.views.course_view import (
    CourseListAPIView, CourseDetailAPIView,
    CourseDeleteAPIView, CourseUpdateAPIView, CourseCreateView,
)
from core.views.topic_view import (
    TopicListAPIView, TopicCreateAPIView,
    TopicDeleteAPIView, TopicUpdateAPIView,
)
from core.views.lesson_view import (
    LessonCreateView, LessonDetailView,
    LessonUpdateView, LessonDeleteView,
    TopicItemsView,
)
from core.views.submission_view import SubmitChallengeView
from core.views.run_code_view import RunCodeView
from core.views.certificate_view import CourseCertificateView, CourseCertificateDownloadView
from core.views.enrollment_view import CourseStudentsView, CourseStudentRemoveView
from core.views.bookmark_view import CourseBookmarkToggleView, BookmarkedCoursesView
from core.views.feedback_view import (
    CourseFeedbackListView, CourseFeedbackCreateView,
    CourseFeedbackUpdateView, CourseFeedbackDeleteView,
)


urlpatterns = [
    # Courses
    path('courses/', CourseListAPIView.as_view(), name='course-list'),
    path('courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('courses/bookmarked/', BookmarkedCoursesView.as_view(), name='course-bookmarked'),
    path('courses/<slug:slug>/', CourseDetailAPIView.as_view(), name='course-detail'),
    path('courses/<slug:slug>/update/', CourseUpdateAPIView.as_view(), name='course-update'),
    path('courses/<slug:slug>/delete/', CourseDeleteAPIView.as_view(), name='course-delete'),
    path('courses/<slug:slug>/certificate/', CourseCertificateView.as_view(), name='course-certificate'),
    path('courses/<slug:slug>/certificate/download/', CourseCertificateDownloadView.as_view(), name='course-certificate-download'),
    path('courses/<slug:slug>/students/', CourseStudentsView.as_view(), name='course-students'),
    path('courses/<slug:slug>/students/<str:username>/', CourseStudentRemoveView.as_view(), name='course-student-remove'),
    path('courses/<slug:slug>/bookmark/', CourseBookmarkToggleView.as_view(), name='course-bookmark'),
    path('courses/<slug:slug>/feedback/', CourseFeedbackListView.as_view(), name='course-feedback-list'),
    path('courses/<slug:slug>/feedback/submit/', CourseFeedbackCreateView.as_view(), name='course-feedback-create'),
    path('courses/<slug:slug>/feedback/mine/', CourseFeedbackUpdateView.as_view(), name='course-feedback-update'),
    path('courses/<slug:slug>/feedback/delete/', CourseFeedbackDeleteView.as_view(), name='course-feedback-delete'),

    # Topics
    path('topics/create/', TopicCreateAPIView.as_view(), name='topic-create'),
    path('topics/<slug:slug>/', TopicListAPIView.as_view(), name='topic-list'),
    path('topics/<slug:slug>/delete/', TopicDeleteAPIView.as_view(), name='topic-delete'),
    path('topics/<slug:slug>/update/', TopicUpdateAPIView.as_view(), name='topic-update'),
    path('topics/<slug:slug>/items/', TopicItemsView.as_view(), name='topic-items'),

    # Lessons
    path('lessons/create/', LessonCreateView.as_view(), name='lesson-create'),
    path('lessons/<slug:slug>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<slug:slug>/update/', LessonUpdateView.as_view(), name='lesson-update'),
    path('lessons/<slug:slug>/delete/', LessonDeleteView.as_view(), name='lesson-delete'),

    # Challenges
    path('challenge/create/', ChallengeCreateAPIView.as_view(), name='challenge-create'),
    path('challenge/create-code/', ChallengeCreateView.as_view(), name='challenge-create-code'),
    path('topics/<slug:slug>/challenges/', ChallengeListAPIView.as_view(), name='challenge-list'),
    path('challenges/<slug:slug>/check/', ChallengeAnswerCheckAPIView.as_view(), name='challenge-check'),
    path('challenges/<slug:slug>/run/', RunCodeView.as_view(), name='challenge-run'),
    path('challenges/<slug:slug>/submit/', SubmitChallengeView.as_view(), name='challenge-submit'),
    path('challenges/<slug:slug>/use-hint/', UseHintView.as_view(), name='challenge-use-hint'),
    path('challenges/<slug:slug>/reveal-solution/', RevealSolutionView.as_view(), name='challenge-reveal-solution'),
    path('challenges/<slug:slug>/update/', ChallengeUpdateAPIView.as_view(), name='challenge-update'),
    path('challenges/<slug:slug>/delete/', ChallengeDeleteAPIView.as_view(), name='challenge-delete'),
]
