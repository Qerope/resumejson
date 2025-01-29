# Use a base Python image
FROM python:3.9-slim as python-base

# Set environment variables for non-interactive installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Python and Node.js (including Playwright's browser dependencies)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libx11-dev \
    libxkbfile-dev \
    libsecret-1-dev \
    libxcomposite-dev \
    libxrandr-dev \
    libxss1 \
    libasound2 \
    libnss3 \
    libgtk-3-0 \
    libgbm-dev \
    libxtst6 \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for the npm install command)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set the working directory for the app
WORKDIR /app

# Copy the app's code into the container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install gradio cohere pyppeteer playwright

RUN npm install -g resume-cli

# Install Node.js dependencies
RUN npm install

# Install Playwright browsers (the Playwright package requires this to run)
RUN python -m playwright install

# Expose the port that the app will run on
EXPOSE 7860

# Command to run the application (modify this if your app has a different entry point)
CMD ["python", "gui-noapi.py"]
