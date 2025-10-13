import os
import sys
import importlib

print("🚀 Setting up Django for Behave tests...")

# 1️⃣ Устанавливаем DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2️⃣ Патчим твой кастомный класс User до загрузки Django
#    (нужно подставить точный путь до твоей модели)
try:
    # Пробуем импортировать модуль с моделью
    user_module = importlib.import_module("authentication.models")

    # Берем сам класс User
    User = getattr(user_module, "User", None)

    # Если атрибута ROLE_CHOICES нет — добавляем
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

# 3️⃣ Теперь можно инициализировать Django
import django
django.setup()

print("✅ Django successfully initialized for Behave tests.")

def before_all(context):
    pass
