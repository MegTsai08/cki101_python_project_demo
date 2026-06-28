# Use Python 3.11.8 as the base image to match the project's Python version
FROM python:3.11.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose port 5000 for Flask
EXPOSE 5000

# Set environment variable to ensure output is printed to terminal
ENV PYTHONUNBUFFERED=1

# Command to run the Flask application
CMD ["python", "app.py"]
