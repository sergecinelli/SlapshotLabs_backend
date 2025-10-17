# Use the official Python runtime image
FROM public.ecr.aws/docker/library/python:3.13
 
# Create the app directory
RUN mkdir /app
 
# Set the working directory inside the container
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
 
# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 
 
# Upgrade pip
RUN pip install --upgrade pip

RUN pip install uvicorn
 
# Copy requirements first to leverage Docker cache
COPY hockey_baseball_app_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project to the container
COPY hockey_baseball_app_backend/ /app/

# Create data directory for mounted database
# RUN mkdir -p /app/data

# Expose the Django port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/sh\n\
echo "Starting Django application..."\n\
python manage.py collectstatic --noinput\n\
python manage.py migrate\n\
python manage.py migrate hockey --database hockey\n\
echo "Starting uvicorn server on port ${PORT:-8000}..."\n\
exec uvicorn hockey_baseball_app_backend.asgi:application --host 0.0.0.0 --port ${PORT:-8000} --log-level info' > /app/start.sh && \
chmod +x /app/start.sh

# Add health check for App Runner
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

# Run startup script
CMD ["/app/start.sh"]
