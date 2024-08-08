# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# UPGRADE pip3
RUN pip3 install --upgrade pip

RUN pip install msal

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app code into the container
COPY . .

# Expose the port on which the app will run
EXPOSE 8003

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8003"]