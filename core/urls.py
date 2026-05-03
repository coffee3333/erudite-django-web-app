from django.urls import path
from core.views.course_view import CourseUpdateAPIView, CourseCreateView
from core.views.challenge_view import ChallengeListAPIView
from core.views.submission_view import SubmitChallengeView, RevealSolutionView, UseHintView
from core.views.bookmark_view import CourseBookmarkToggleView, BookmarkedCoursesView
from core.views.feedback_view import CourseFeedbackListView, CourseFeedbackCreateView

urlpatterns = [
    path('courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('courses/<slug:slug>/update/', CourseUpdateAPIView.as_view(), name='course-update'),
    path('courses/<slug:slug>/bookmark/', CourseBookmarkToggleView.as_view(), name='course-bookmark'),
    path('courses/<slug:slug>/feedback/', CourseFeedbackListView.as_view(), name='course-feedback'),
    path('courses/bookmarked/', BookmarkedCoursesView.as_view(), name='courses-bookmarked'),
    path('topics/<slug:slug>/challenges/', ChallengeListAPIView.as_view(), name='topic-challenges'),
    path('challenges/<slug:slug>/submit/', SubmitChallengeView.as_view(), name='challenge-submit'),
    path('challenges/<slug:slug>/reveal-solution/', RevealSolutionView.as_view(), name='challenge-reveal-solution'),
    path('challenges/<slug:slug>/use-hint/', UseHintView.as_view(), name='challenge-use-hint'),
]

