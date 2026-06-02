# Use a stable, lightweight Python image
FROM python:3.10-slim

# Set the directory inside the container
WORKDIR /app

# Copy requirements first to save build cache memory
COPY requirements.txt .

# Install dependencies cleanly
RUN pip install --no-cache-dir -r requirements.txt

# Copy all local project files into the container
COPY . .

# Expose Flask's default port
EXPOSE 5000

# Start the production gateway with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]