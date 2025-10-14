from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse


class Course(models.Model):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_courses"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    language = models.CharField(max_length=30, default="en")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="beginner")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    featured_image = models.ImageField(
        upload_to="courses/",
        blank=True,
        null=True,
        help_text="Featured image for the course (max 5MB, JPEG/PNG)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["slug"]),
        ]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def save(self, *args, **kwargs):
        if not self.title or not self.title.strip():
            raise ValueError("Course title cannot be empty.")

        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug or "course"
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course-detail", kwargs={"slug": self.slug})
