# core/models/lesson.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Lesson(models.Model):
    CONTENT_TYPE_CHOICES = [
        ("text",  "Text / Markdown"),
        ("video", "Video"),
        ("mixed", "Text + Video"),
    ]
    topic            = models.ForeignKey("Topic", on_delete=models.CASCADE, related_name="lessons")
    owner            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title            = models.CharField(max_length=200)
    slug             = models.SlugField(max_length=220, unique=True)
    content          = models.TextField(blank=True)          # Markdown body
    video_url        = models.URLField(blank=True, null=True)
    content_type     = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default="text")
    photo            = models.ImageField(upload_to="lesson_photos/", blank=True, null=True)
    sort_order       = models.PositiveIntegerField(default=0) # shared with Challenge.sort_order
    estimated_minutes = models.PositiveIntegerField(default=5)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "lesson"
            slug = base_slug
            counter = 1
            while Lesson.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)