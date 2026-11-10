FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code (agent.py plus the provider/tool modules it imports)
COPY agent.py providers.py agent_tools.py .

# Run the agent
CMD ["python", "agent.py", "start"]
