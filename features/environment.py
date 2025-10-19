import os
import sys
import importlib

print("🚀 Setting up Django for Behave tests...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    user_module = importlib.import_module("authentication.models")
    User = getattr(user_module, "User", None)

    if User and not hasattr(User, "ROLE_CHOICES"):
        print("⚙️ Injecting ROLE_CHOICES into custom User model...")
        User.ROLE_CHOICES = [
            ("student", "Student"),
            ("teacher", "Teacher"),
            ("admin", "Admin"),
        ]
        print("✅ ROLE_CHOICES successfully injected.")
except Exception as e:
    print(f"⚠️ Could not inject ROLE_CHOICES early: {e}")

import django
django.setup()

print("✅ Django successfully initialized for Behave tests.")

def before_all(context):
    pass
