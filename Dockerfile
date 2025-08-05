# Dockerfile לבוט הפרסום האוטומטי
# תמונה בסיסית: Python 3.11 על Ubuntu slim
FROM python:3.11-slim

# מידע על התמונה
LABEL maintainer="your-email@example.com"
LABEL description="Social Media Auto-Posting Bot"
LABEL version="1.0"

# הגדרת משתני סביבה
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# הגדרת תיקיית עבודה
WORKDIR /app

# עדכון מערכת והתקנת תלויות מערכת
RUN apt-get update && apt-get install -y \
    # כלים בסיסיים
    curl \
    wget \
    git \
    # עיבוד מדיה
    ffmpeg \
    libavcodec-extra \
    # עיבוד תמונות
    libjpeg-dev \
    libpng-dev \
    # כלי פיתוח
    gcc \
    g++ \
    # ניקוי cache
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# יצירת משתמש לא-root לאבטחה
RUN groupadd -r botuser && useradd -r -g botuser -d /app -s /bin/bash botuser

# יצירת תיקיות נדרשות
RUN mkdir -p /app/temp /app/logs && \
    chown -R botuser:botuser /app

# העתקת requirements.txt והתקנת תלויות Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת קבצי הפרויקט
COPY . .

# הגדרת הרשאות
RUN chown -R botuser:botuser /app && \
    chmod +x /app/main.py

# מעבר למשתמש לא-root
USER botuser

# חשיפת פורט (למקרה שנרצה health check)
EXPOSE 8080

# הגדרת health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from database import get_database; db = get_database(); exit(0 if db.health_check() else 1)" || exit 1

# נקודת כניסה ברירת מחדל
ENTRYPOINT ["python", "main.py"]

# פקודת ברירת מחדל (ניתן לעקוף)
CMD []

# ============================================================================
# הוראות שימוש
# ============================================================================

# בניית התמונה:
# docker build -t social-media-bot .

# הרצה עם docker run:
# docker run -d \
#   --name social-bot \
#   --env-file .env \
#   -v $(pwd)/logs:/app/logs \
#   -v $(pwd)/temp:/app/temp \
#   --restart unless-stopped \
#   social-media-bot

# הרצה עם docker-compose (ראו docker-compose.yml):
# docker-compose up -d

# צפייה בלוגים:
# docker logs -f social-bot

# כניסה לקונטיינר:
# docker exec -it social-bot bash

# עצירה וחידוש:
# docker restart social-bot

# ============================================================================
# Docker Compose דוגמה (צרו קובץ docker-compose.yml)
# ============================================================================

# version: '3.8'
# 
# services:
#   social-media-bot:
#     build: .
#     container_name: social-bot
#     restart: unless-stopped
#     env_file:
#       - .env
#     volumes:
#       - ./logs:/app/logs
#       - ./temp:/app/temp
#     environment:
#       - LOG_LEVEL=INFO
#       - MOCK_MODE=false
#     healthcheck:
#       test: ["CMD", "python", "-c", "from database import get_database; db = get_database(); exit(0 if db.health_check() else 1)"]
#       interval: 30s
#       timeout: 10s
#       retries: 3
#       start_period: 60s
#     # אם רוצים health check endpoint:
#     # ports:
#     #   - "8080:8080"
# 
#   # MongoDB (אופציונלי - אם לא משתמשים ב-Atlas)
#   mongodb:
#     image: mongo:5.0
#     container_name: social-bot-mongo
#     restart: unless-stopped
#     environment:
#       MONGO_INITDB_ROOT_USERNAME: admin
#       MONGO_INITDB_ROOT_PASSWORD: password123
#       MONGO_INITDB_DATABASE: social_media_bot
#     volumes:
#       - mongodb_data:/data/db
#     ports:
#       - "27017:27017"
# 
# volumes:
#   mongodb_data:

# ============================================================================
# Multi-stage build (אופציונלי - לאופטימיזציה)
# ============================================================================

# אם רוצים תמונה קטנה יותר, אפשר להשתמש ב-multi-stage build:

# # Stage 1: Builder
# FROM python:3.11-slim as builder
# 
# WORKDIR /app
# 
# # התקנת תלויות build
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     libjpeg-dev \
#     libpng-dev \
#     && rm -rf /var/lib/apt/lists/*
# 
# COPY requirements.txt .
# RUN pip install --user --no-cache-dir -r requirements.txt
# 
# # Stage 2: Runtime
# FROM python:3.11-slim
# 
# # העתקת תלויות Python מהbuilder
# COPY --from=builder /root/.local /root/.local
# 
# # הוספת Python packages לPATH
# ENV PATH=/root/.local/bin:$PATH
# 
# # התקנת תלויות runtime בלבד
# RUN apt-get update && apt-get install -y \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*
# 
# WORKDIR /app
# 
# # העתקת קבצי האפליקציה
# COPY . .
# 
# CMD ["python", "main.py"]

# ============================================================================
# הגדרות אבטחה מתקדמות
# ============================================================================

# אם רוצים אבטחה מוגברת:

# FROM python:3.11-slim
# 
# # שימוש ב-non-root user מההתחלה
# RUN groupadd -r -g 1000 botuser && \
#     useradd -r -g botuser -u 1000 -m -d /app botuser
# 
# # הגדרת קבצי מערכת לread-only
# RUN apt-get update && apt-get install -y \
#     ffmpeg \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/* \
#     && chmod -R go-rwx /app
# 
# USER botuser
# WORKDIR /app
# 
# # הגבלת capabilities
# # RUN setcap cap_net_bind_service=+ep /usr/local/bin/python
# 
# # רק קבצים נדרשים
# COPY --chown=botuser:botuser requirements.txt .
# RUN pip install --user --no-cache-dir -r requirements.txt
# COPY --chown=botuser:botuser . .
# 
# # filesystem read-only
# # docker run --read-only --tmpfs /tmp --tmpfs /app/temp social-media-bot

# ============================================================================
# Variables שימושיות
# ============================================================================

# הגדרת משתני build-time (אופציונלי):
# ARG BUILD_DATE
# ARG VCS_REF
# ARG VERSION
# 
# LABEL org.label-schema.build-date=$BUILD_DATE \
#       org.label-schema.name="social-media-bot" \
#       org.label-schema.description="Automated social media posting bot" \
#       org.label-schema.vcs-ref=$VCS_REF \
#       org.label-schema.vcs-url="https://github.com/your-username/social-media-bot" \
#       org.label-schema.version=$VERSION \
#       org.label-schema.schema-version="1.0"

# שימוש:
# docker build \
#   --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
#   --build-arg VCS_REF=$(git rev-parse --short HEAD) \
#   --build-arg VERSION=1.0.0 \
#   -t social-media-bot:1.0.0 .

# ============================================================================
# טיפים לאופטימיזציה
# ============================================================================

# 1. שימוש ב-.dockerignore:
# צרו קובץ .dockerignore עם:
# .git
# .gitignore
# README.md
# Dockerfile
# .dockerignore
# .env
# .env.*
# temp/
# logs/
# __pycache__/
# *.pyc
# .pytest_cache/
# .coverage
# .vscode/
# .idea/

# 2. מיון שכבות לפי תדירות שינוי:
# - תלויות מערכת (משתנות פחות)
# - requirements.txt (משתנה לפעמים)
# - קוד האפליקציה (משתנה הכי הרבה)

# 3. שימוש ב-cache mounts (Docker BuildKit):
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install -r requirements.txt

# 4. הפחתת שכבות:
# RUN apt-get update && apt-get install -y package1 package2 \
#     && rm -rf /var/lib/apt/lists/*

# ============================================================================
# פתרון בעיות נפוצות
# ============================================================================

# בעיה: "Permission denied" 
# פתרון: ודאו שהמשתמש botuser יש הרשאות לתיקיות

# בעיה: "Module not found"
# פתרון: ודאו שכל requirements.txt נכלל ומתותקן

# בעיה: "Cannot connect to MongoDB"
# פתרון: השתמשו ב-docker-compose עם MongoDB או Atlas

# בעיה: קונטיינר נעצר מיד
# פתרון: בדקו logs עם docker logs <container>

# בעיה: גודל תמונה גדול
# פתרון: השתמשו ב-multi-stage build או alpine image

# ============================================================================
# פקודות שימושיות
# ============================================================================

# בניה מחדש ללא cache:
# docker build --no-cache -t social-media-bot .

# ניקוי תמונות ישנות:
# docker image prune -a

# צפייה בגודל תמונה:
# docker images social-media-bot

# ייצוא/ייבוא תמונה:
# docker save social-media-bot > social-bot.tar
# docker load < social-bot.tar

# פרסום ל-Docker Hub:
# docker tag social-media-bot your-username/social-media-bot:latest
# docker push your-username/social-media-bot:latest

# ============================================================================
# הגדרות פרודקשן
# ============================================================================

# עבור פרודקשן, מומלץ:

# 1. תמונת בסיס מינימלית:
# FROM python:3.11-alpine
# (אבל זה מסובך יותר - צריך להתקין build tools)

# 2. משתמש dedicated:
# RUN adduser -D -s /bin/sh botuser

# 3. הגבלת משאבים:
# docker run --memory=512m --cpus="1.0" social-media-bot

# 4. restart policy:
# docker run --restart=always social-media-bot

# 5. monitoring:
# docker run --log-driver=fluentd social-media-bot

# 6. secrets management:
# docker run --env-file=/secure/path/.env social-media-bot
