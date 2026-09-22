FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     curl     && rm -rf /var/lib/apt/lists/*

# Set up non-root user for Hugging Face Spaces security
RUN useradd -m -u 1000 user
ENV HOME=/home/user     PATH=/home/user/.local/bin:$PATH     PYTHONUNBUFFERED=1     PORT=7860

WORKDIR /app

# Install python dependencies as user
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy all project code, datasets, protocols, and frontend
COPY --chown=user:user . .

# Expose Hugging Face Space standard port
EXPOSE 7860

# Launch uvicorn on port 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
