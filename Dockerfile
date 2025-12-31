# Purpose of this Docker File is to create Docker Image (also called docket snapshoy) 
# which is nothing but docker container compatible instruction and 
# will be executed inside Docker Container. You can pull this image in Docker Desktop -> Container
# -> Pull the image - >Run the image
# Use official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir. Name of the directory is app
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y build-essential poppler-utils && rm -rf /var/lib/apt/lists/*

# Copy requirements. See the "." after a space. It means current directory
COPY requirements.txt .

# Copy project files. ***THIS IS IMPORTANT** COPYING ALL PROJECT FILES
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8080

# Run FastAPI with uvicorn
#CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

# Replace last CMD in prod
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
