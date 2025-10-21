# Use the official Python runtime image
FROM public.ecr.aws/docker/library/python:3.13
 
# Create the app directory
RUN mkdir /app
 
# Set the working directory inside the container
WORKDIR /app

# RUN apt-get update
# RUN apt-get install -y necessary_package
 
# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 
 
# Upgrade pip
RUN pip install --upgrade pip

RUN pip install uvicorn
 
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project to the container
COPY . /app/

# Create data directory for mounted database
# RUN mkdir -p /app/data

# Expose the Django port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/sh\n\
python manage.py collectstatic --noinput\n\
python manage.py migrate\n\
python manage.py migrate hockey --database hockey\n\
exec uvicorn hockey_baseball_app_backend.asgi:application --host 0.0.0.0 --port 8000 --log-level debug' > /app/start.sh && \
chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]
