from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.text import slugify
from django.urls import reverse

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, role="student", **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        if not role:
            raise ValueError("Role is required")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("teacher", "Teacher"),
    )
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    user_bio = models.CharField(max_length=255, blank=True, null=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True, default='user_photos/default_mdlthc.png')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    email_verified = models.BooleanField(default=False)
    slug = models.SlugField(max_length=60, unique=True, blank=True, help_text="URL-friendly user slug.")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.username)
            slug = base_slug or "user"
            counter = 1
            while User.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def get_absolute_url(self):
        return reverse('user-detail', kwargs={'slug': self.slug})

    # def count_followers(self):
    #     return self.followers.count() if hasattr(self, 'followers') else 0
    #
    # def count_following(self):
    #     return self.following.count() if hasattr(self, 'following') else 0
    #
    # def count_recipes(self):
    #     return self.recipes.count() if hasattr(self, 'recipes') else 0
    #




class PasswordResetOTP(models.Model):
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return (timezone.now() - self.created_at).total_seconds() < 600 and not self.is_used


class EmailVerificationCode(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at).seconds < 600
