#!/bin/bash

echo "=========================================="
echo "Voice Agent Setup Script"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi
echo "✅ Docker is running"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
    echo "   - TWILIO_ACCOUNT_SID"
    echo "   - TWILIO_AUTH_TOKEN"
    echo "   - TWILIO_PHONE_NUMBER"
    echo "   - OPENAI_API_KEY"
    echo "   - PUBLIC_URL (from ngrok)"
    echo ""
    echo "Run this script again after updating .env"
    exit 0
else
    echo "✅ Found .env file"
fi

# Check if ngrok URL is configured
if grep -q "your-ngrok-url" .env; then
    echo ""
    echo "⚠️  WARNING: PUBLIC_URL not configured in .env"
    echo ""
    echo "Please:"
    echo "1. Start ngrok: ngrok http 8000"
    echo "2. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)"
    echo "3. Update PUBLIC_URL in .env"
    echo ""
    read -p "Have you updated PUBLIC_URL? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo ""
echo "Building Docker containers..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi
echo "✅ Docker containers built successfully"

echo ""
echo "Starting services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services!"
    exit 1
fi

echo "✅ Services started successfully"
echo ""
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Your voice agent is running at:"
echo "  http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo ""
echo "Make sure ngrok is still running!"
echo "If ngrok restarts, update PUBLIC_URL in .env"
echo ""
