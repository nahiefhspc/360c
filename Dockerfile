# Use Python base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for Flask
ENV FLASK_APP=main.py

# Expose port
EXPOSE 8080

# Run the bot & Flask app
CMD ["python3", "main.py"]
