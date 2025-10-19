# Erudite Backend

Erudite Backend is the server-side application for the Erudite education platform, built with Django and Django REST Framework.
It uses PostgreSQL as the database and is intended to be run exclusively via Docker.

---
## 🚀 Features

- REST API for challenges, users, comments, and more
- JWT authentication, Google OAuth
- Media file storage (images)
- Modern, scalable project structure

---
## 🛠️ Tech Stack

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## 📦 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/coffee3333/tech-blog-django.git
cd intech-blog-backend
```

### 2. Configure environment variables

```
DEBUG=False

SECRET_KEY='Your secret key for app'
ALLOWED_HOSTS=*

EMAIL_HOST_USER='SMTP credentials'
EMAIL_HOST_PASSWORD='SMTP pass'

CLOUDINARY_CLOUD_NAME=''
CLOUDINARY_API_KEY=''
CLOUDINARY_API_SECRET=''

GOOGLE_CLIENT_ID=''
GOOGLE_CLIENT_SECRET=''

DB_HOST=db
DB_USER=postgres
DB_PASSWORD=postgres_password
DB_NAME=postgres
DB_PORT=5432

POSTGRES_HOST_AUTH_METHOD=trust
```

### 2. Start the backend

```bash
  docker compose up
```


## 📝 Useful Commands


- Stop the project:
docker compose down

- View logs:
docker compose logs -f

## 📜 API Documentation
API documentation (Swagger) is available at:
/swagger/

## 📎 References
[Erudite Documentation](https://github.com/Ngoc901/erudite-documentation)  


## 🧑‍💻 Author
    Niki aka Huawei
    Brian aka Briana
    Atai aka Alter
