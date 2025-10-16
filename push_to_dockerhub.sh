#!/bin/bash
set -e

echo "=== Docker Hub Push Script ==="
echo ""
echo "This script will push your voice-agents images to Docker Hub"
echo ""

# Check if logged in
if ! grep -q "index.docker.io" ~/.docker/config.json 2>/dev/null; then
    echo "❌ Not logged in to Docker Hub"
    echo ""
    echo "Please login first with:"
    echo "  docker login"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Docker login detected"
echo ""

# Verify images exist
echo "Checking if images exist..."
if ! docker images | grep -q "kpanse/voice-agents-app.*latest"; then
    echo "❌ Image kpanse/voice-agents-app:latest not found"
    echo "Building app image..."
    docker compose build app
fi

if ! docker images | grep -q "kpanse/voice-agents-livekit-agent.*latest"; then
    echo "❌ Image kpanse/voice-agents-livekit-agent:latest not found"
    echo "Building livekit-agent image..."
    docker compose build livekit-agent
fi

echo "✅ Images found"
echo ""

# Show image sizes
echo "Images to push:"
docker images | grep -E "kpanse/voice-agents-(app|livekit-agent)"
echo ""

# Push app image (latest)
echo "📤 Pushing kpanse/voice-agents-app:latest (929MB)..."
docker push kpanse/voice-agents-app:latest
echo "✅ App image (latest) pushed"
echo ""

# Tag and push app image (v1.0)
echo "🏷️  Tagging kpanse/voice-agents-app:v1.0..."
docker tag kpanse/voice-agents-app:latest kpanse/voice-agents-app:v1.0
echo "📤 Pushing kpanse/voice-agents-app:v1.0..."
docker push kpanse/voice-agents-app:v1.0
echo "✅ App image (v1.0) pushed"
echo ""

# Push livekit-agent image (latest)
echo "📤 Pushing kpanse/voice-agents-livekit-agent:latest (1.27GB)..."
docker push kpanse/voice-agents-livekit-agent:latest
echo "✅ LiveKit agent image (latest) pushed"
echo ""

# Tag and push livekit-agent image (v1.0)
echo "🏷️  Tagging kpanse/voice-agents-livekit-agent:v1.0..."
docker tag kpanse/voice-agents-livekit-agent:latest kpanse/voice-agents-livekit-agent:v1.0
echo "📤 Pushing kpanse/voice-agents-livekit-agent:v1.0..."
docker push kpanse/voice-agents-livekit-agent:v1.0
echo "✅ LiveKit agent image (v1.0) pushed"
echo ""

echo "🎉 All images pushed to Docker Hub!"
echo ""
echo "Images now available at:"
echo "  - https://hub.docker.com/r/kpanse/voice-agents-app"
echo "  - https://hub.docker.com/r/kpanse/voice-agents-livekit-agent"
echo ""
echo "Anyone can now pull and deploy with:"
echo "  docker pull kpanse/voice-agents-app:latest"
echo "  docker pull kpanse/voice-agents-livekit-agent:latest"
echo "  docker compose -f docker-compose.prod.yml up -d"
