from django.contrib import admin

from .models.challenge_option import ChallengeOption
from .models.course_model import Course
from .models.topic_model import Topic
from .models.submission_model import Submission
from .models.challenge_model import Challenge
from .models.challenge_correct_answer import ChallengeCorrectAnswer
from .models.lesson import Lesson
from .models.code_challenge import CodeChallengeConfig, CodeTestCase, CodeSubmissionResult
from .models.certificate_model import Certificate


admin.site.register(Course)
admin.site.register(Topic)
admin.site.register(Submission)
admin.site.register(Challenge)
admin.site.register(ChallengeCorrectAnswer)
admin.site.register(ChallengeOption)
admin.site.register(Lesson)
admin.site.register(CodeChallengeConfig)
admin.site.register(CodeTestCase)
admin.site.register(CodeSubmissionResult)
admin.site.register(Certificate)
