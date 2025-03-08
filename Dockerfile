# Use official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Start the bot
CMD ["python3", "main.py"]
