# Use an official lightweight Python Alpine image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Install build dependencies (required for some Python packages)
RUN apk add --no-cache gcc musl-dev linux-headers

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Run the application with Gunicorn as the production WSGI server
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
