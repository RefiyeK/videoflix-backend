# Videoflix Backend

A Django REST Framework backend for a video streaming platform. It handles user
registration with email activation, JWT authentication via HttpOnly cookies,
password reset by email, and video streaming over HLS. Account activation and
password reset are sent as branded, responsive HTML emails. Uploaded videos are
converted to HLS (480p / 720p / 1080p) in the background using FFMPEG and a
Redis-backed task queue.

The frontend is **not** part of this repository. It was provided by Developer
Akademie and is run separately (see [Running the frontend](#running-the-frontend)).

## Tech stack

- **Django 5.2** + **Django REST Framework**
- **PostgreSQL 16** (database)
- **Redis 7** (cache and task broker)
- **Django-RQ** (background task queue)
- **FFMPEG** (HLS video conversion)
- **SimpleJWT** with HttpOnly cookies (authentication)
- **SMTP email** with responsive HTML templates (activation and password reset)
- **Docker** + **Docker Compose** (the whole stack runs in containers)

## Requirements

You only need these installed on your machine:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/) (bundled with Docker Desktop)
- [Git](https://git-scm.com/)

Everything else (Python, FFMPEG, PostgreSQL, Redis) runs inside the containers.

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/RefiyeK/videoflix-backend.git
cd videoflix-backend
```

### 2. Create your environment file

Copy the template and fill in your own values:

```bash
cp .env.template .env
```

Then open `.env` and set the values. The variables are:

| Variable | Description | Example |
| --- | --- | --- |
| `SECRET_KEY` | Django secret key (generate a new one, see below) | `django-insecure-...` |
| `DEBUG` | Debug mode; use `True` locally | `True` |
| `DB_NAME` | PostgreSQL database name | `videoflix_db` |
| `DB_USER` | PostgreSQL user | `videoflix_user` |
| `DB_PASSWORD` | PostgreSQL password | `your-db-password` |
| `DB_HOST` | Database host (the compose service name) | `db` |
| `DB_PORT` | Database port | `5432` |
| `REDIS_HOST` | Redis host (the compose service name) | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `EMAIL_BACKEND` | Django email backend | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | Use TLS for email | `True` |
| `EMAIL_HOST_USER` | SMTP account (your email) | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password (see note below) | `abcd efgh ijkl mnop` |
| `DEFAULT_FROM_EMAIL` | The "from" address on outgoing mail | `Videoflix <your-email@gmail.com>` |
| `FRONTEND_URL` | Base URL of the running frontend | `http://127.0.0.1:5500` |

> **`DB_HOST` and `REDIS_HOST` must be `db` and `redis`** (the Docker Compose
> service names), not `localhost`. Inside the container, the database is reached
> by its service name.

**Generating a `SECRET_KEY`:** you can produce one with Python:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Email / Gmail note:** if you use Gmail, `EMAIL_HOST_PASSWORD` is **not** your
normal Gmail password. You need a 16-character
[App Password](https://support.google.com/accounts/answer/185833) generated for
your Google account (2-step verification must be enabled). Without valid email
credentials, registration and password reset will fail to send mail.

### 3. Start the containers

```bash
docker compose up --build
```

This builds the image (installing FFMPEG and Python dependencies) and starts four
services: `web` (Django), `db` (PostgreSQL), `redis`, and `rq-worker` (the
background worker that runs video conversion and email sending).

Database **migrations run automatically** on startup (via `entrypoint.sh`), so you
don't need to run them by hand. When you see a line like
`Starting development server at http://0.0.0.0:8000/`, the backend is ready.

The API is now available at **http://127.0.0.1:8000/api/**.

> On later starts you can drop `--build` and just run `docker compose up`. Use
> `--build` again only after changing `requirements.txt` or the `Dockerfile`.

### 4. Create an admin user

To upload videos and access the Django admin, create a superuser. In a **second
terminal** (leave `docker compose up` running in the first):

```bash
docker compose exec web python manage.py createsuperuser
```

Because this project uses an **email-based user model**, you log in with an email
address instead of a username.

### 5. Upload a video

1. Open the admin at **http://127.0.0.1:8000/admin/** and log in.
2. Go to **Videos** and add a new video: set a title, description, category,
   thumbnail image, and upload a video file.
3. On save, the `rq-worker` automatically converts the video to HLS in 480p,
   720p, and 1080p. You can watch the progress in the `docker compose up` log.
   Conversion takes a little while depending on the video length.

Once conversion is done, the video is available for streaming through the API and
the frontend.

## Running the frontend

The frontend is a separate project provided by Developer Akademie. Fork/clone it,
then serve it with a static server such as the VS Code **Live Server** extension
on port **5500**, so it runs at `http://127.0.0.1:5500`.

Make sure `FRONTEND_URL` in your `.env` matches the address the frontend runs on,
because activation and password-reset links in emails point there.

## API endpoints

Base URL: `http://127.0.0.1:8000/api/`

### Authentication

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/register/` | Register a new (inactive) user and send an activation email | No |
| `GET` | `/activate/<uidb64>/<token>/` | Activate an account with the emailed token | No |
| `POST` | `/login/` | Log in; sets `access_token` and `refresh_token` HttpOnly cookies | No |
| `POST` | `/logout/` | Log out; clears cookies and blacklists the refresh token | Cookie |
| `POST` | `/token/refresh/` | Issue a new access token from the refresh cookie | Cookie |
| `POST` | `/password_reset/` | Send a password reset email | No |
| `POST` | `/password_confirm/<uidb64>/<token>/` | Set a new password using the emailed token | No |

### Video

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `GET` | `/video/` | List all available videos (newest first) | JWT |
| `GET` | `/video/<movie_id>/<resolution>/index.m3u8` | HLS master playlist for a resolution | JWT |
| `GET` | `/video/<movie_id>/<resolution>/<segment>.ts` | A single HLS video segment | JWT |

Video endpoints require a valid `access_token` cookie. Without it they return
`401 Unauthorized`.

## Running tests

The test suite runs inside the `web` container. With the stack up:

```bash
docker compose exec web python manage.py test
```

To run the tests for a single app:

```bash
docker compose exec web python manage.py test authentication_app
docker compose exec web python manage.py test video_app
```

To measure coverage:

```bash
docker compose exec web coverage run --source='authentication_app,video_app' manage.py test
docker compose exec web coverage report -m
```

## Linting

The project follows PEP 8, checked with flake8:

```bash
docker compose exec web flake8 authentication_app/ --exclude=migrations
docker compose exec web flake8 video_app/ --exclude=migrations
```

## Project structure

```
backend/
├── core/                  # Project settings, root URLs, WSGI/ASGI
├── authentication_app/    # User model, auth endpoints, email helpers
│   └── api/               # Serializers, views, URLs
├── video_app/             # Video model, HLS conversion, streaming endpoints
│   ├── api/               # Serializers, views, URLs
│   ├── services.py        # FFMPEG conversion and file-path helpers
│   ├── tasks.py           # Background RQ task
│   └── signals.py         # Triggers conversion on upload
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh          # Runs migrations, then the container command
├── requirements.txt
└── .env.template          # Copy to .env and fill in
```

## Notes

- `.env` is never committed. Only `.env.template` (with placeholder values) is in
  the repository. Never commit real secrets.
- Media files (uploaded videos, generated HLS segments, thumbnails) are stored in
  `media/`, which is git-ignored.
- The Docker setup was provided by Developer Akademie and should not be modified.