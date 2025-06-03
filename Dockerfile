FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dependency declarations
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application into the image
COPY . .

# Run the FastAPI application
CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "80"]

