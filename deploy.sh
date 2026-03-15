#!/bin/bash
# Deploy Agentic Researcher to an EC2 instance
# Usage: ./deploy.sh <EC2_PUBLIC_IP> <path_to_key.pem>

set -e

EC2_IP=$1
KEY_FILE=$2

if [ -z "$EC2_IP" ] || [ -z "$KEY_FILE" ]; then
    echo "Usage: ./deploy.sh <EC2_PUBLIC_IP> <path_to_key.pem>"
    exit 1
fi

echo "=== Step 1: Installing Docker on EC2 ==="
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ec2-user@$EC2_IP << 'EOF'
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
EOF

echo "=== Step 2: Copying files to EC2 ==="
rsync -avz -e "ssh -i $KEY_FILE" \
    --exclude='venv' --exclude='__pycache__' --exclude='.git' \
    --exclude='output' --exclude='*.png' \
    ./ ec2-user@$EC2_IP:~/agentic-researcher/

echo "=== Step 3: Building and running on EC2 ==="
ssh -i "$KEY_FILE" ec2-user@$EC2_IP << EOF
cd ~/agentic-researcher
sudo docker build -t agentic-researcher .
sudo docker stop researcher 2>/dev/null || true
sudo docker rm researcher 2>/dev/null || true
sudo docker run -d \
    --name researcher \
    --restart unless-stopped \
    -p 7860:7860 \
    -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    agentic-researcher
EOF

echo ""
echo "=== Done! ==="
echo "App is running at: http://$EC2_IP:7860"
