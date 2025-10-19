from django.db import models
from django.conf import settings
from core.models.course_model import Course
from django.utils.text import slugify


class Topic(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="topics"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topics",
    )
    title = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.course.title} → {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Topic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)