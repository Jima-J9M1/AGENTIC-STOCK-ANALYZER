#!/bin/bash

# ECS FMP MCP Server Setup Script
# Replicates us-east-1 setup to eu-west-2

set -e

# Check for required environment variables or prompt for them
if [ -z "$REGION" ]; then
    echo "REGION not found in environment."
    echo -n "Please enter AWS region (e.g., eu-west-2, us-east-1): "
    read -r REGION
    if [ -z "$REGION" ]; then
        echo "Error: REGION cannot be empty"
        exit 1
    fi
fi

if [ -z "$CLUSTER_NAME" ]; then
    echo "CLUSTER_NAME not found in environment."
    echo -n "Please enter ECS cluster name (e.g., mcp-cluster): "
    read -r CLUSTER_NAME
    if [ -z "$CLUSTER_NAME" ]; then
        echo "Error: CLUSTER_NAME cannot be empty"
        exit 1
    fi
fi

if [ -z "$TASK_FAMILY_SSE" ]; then
    echo "TASK_FAMILY_SSE not found in environment."
    echo -n "Please enter task definition family name for SSE service (e.g., mcp-task): "
    read -r TASK_FAMILY_SSE
    if [ -z "$TASK_FAMILY_SSE" ]; then
        echo "Error: TASK_FAMILY_SSE cannot be empty"
        exit 1
    fi
fi

if [ -z "$TASK_FAMILY_STREAM" ]; then
    echo "TASK_FAMILY_STREAM not found in environment."
    echo -n "Please enter task definition family name for streamable service (e.g., mcp-task-stream): "
    read -r TASK_FAMILY_STREAM
    if [ -z "$TASK_FAMILY_STREAM" ]; then
        echo "Error: TASK_FAMILY_STREAM cannot be empty"
        exit 1
    fi
fi
if [ -z "$FMP_API_KEY" ]; then
    echo "FMP_API_KEY not found in environment."
    echo -n "Please enter your FMP API Key: "
    read -r FMP_API_KEY
    if [ -z "$FMP_API_KEY" ]; then
        echo "Error: FMP_API_KEY cannot be empty"
        exit 1
    fi
fi

if [ -z "$CONTAINER_IMAGE" ]; then
    echo "CONTAINER_IMAGE not found in environment."
    echo -n "Please enter your container image (e.g., ghcr.io/cdtait/fmp-mcp-server:latest): "
    read -r CONTAINER_IMAGE
    if [ -z "$CONTAINER_IMAGE" ]; then
        echo "Error: CONTAINER_IMAGE cannot be empty"
        exit 1
    fi
fi

echo "=== FMP MCP Server ECS Setup ==="
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo "SSE Task Family: $TASK_FAMILY_SSE"
echo "Stream Task Family: $TASK_FAMILY_STREAM"
echo "Container Image: $CONTAINER_IMAGE"
echo "FMP API Key: ${FMP_API_KEY:0:8}... (truncated for security)"
echo ""

# 1. Install/Update AWS CLI v2
echo "Step 1: Installing AWS CLI v2..."
sudo yum remove awscli -y || true
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update
rm -rf awscliv2.zip aws/

# Verify installation
aws --version

echo "Step 1 Complete: AWS CLI installed"

# 2. Configure AWS CLI
echo "Step 2: Configuring AWS CLI..."
echo ""
echo "*** IMPORTANT: IAM Setup Instructions ***"
echo "Before continuing, you need AWS IAM credentials:"
echo ""
echo "1. Log into AWS Console as root user"
echo "2. Go to IAM > Users > Create user"
echo "3. Set username (e.g. 'ecs-cli-user')"
echo "4. Select 'Programmatic access'"
echo "5. Attach these policies directly:"
echo "   - AmazonECS_FullAccess"
echo "   - AmazonEC2ReadOnlyAccess"
echo "   - IAMReadOnlyAccess"
echo "   - CloudWatchReadOnlyAccess"
echo "   - AmazonECSTaskExecutionRolePolicy"
echo "6. Create user and DOWNLOAD the credentials CSV"
echo "7. Note the Access Key ID and Secret Access Key"
echo ""
echo "You will need:"
echo "- AWS Access Key ID"
echo "- AWS Secret Access Key"
echo "- Default region: $REGION"
echo "- Default output format: json"
echo ""

aws configure

echo ""
echo "Step 2 Complete: AWS CLI configured"
echo "Press Enter to continue with ECS setup..."
read

# 3. Verify AWS Configuration
echo "Step 3: Verifying AWS configuration..."
aws sts get-caller-identity --region $REGION
echo "Current region: $(aws configure get region)"

# 4. Create ECS Cluster
echo "Step 4: Creating ECS cluster..."
aws ecs create-cluster \
    --region $REGION \
    --cluster-name $CLUSTER_NAME \
    --capacity-providers FARGATE FARGATE_SPOT

echo "Cluster created: $CLUSTER_NAME"

# 5. Create IAM Execution Role (if not exists)
echo "Step 5: Checking IAM execution role..."
EXECUTION_ROLE_ARN=$(aws iam get-role --role-name ecsTaskExecutionRole --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo "Creating ecsTaskExecutionRole..."
    
    # Create role
    aws iam create-role \
        --role-name ecsTaskExecutionRole \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }'
    
    # Attach policy
    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    EXECUTION_ROLE_ARN=$(aws iam get-role --role-name ecsTaskExecutionRole --query 'Role.Arn' --output text)
    echo "Created execution role: $EXECUTION_ROLE_ARN"
else
    echo "Execution role exists: $EXECUTION_ROLE_ARN"
fi

# 6. Get default VPC and security group
echo "Step 6: Getting VPC configuration..."
VPC_ID=$(aws ec2 describe-vpcs --region $REGION --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text)
SUBNETS=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text | tr '\t' ',')

echo "VPC: $VPC_ID"
echo "Security Group: $SECURITY_GROUP_ID"
echo "Subnets: $SUBNETS"

# 7. Configure security group rules
echo "Step 7: Configuring security group rules..."

# Check if port 8000 rule exists
PORT_8000_EXISTS=$(aws ec2 describe-security-groups --region $REGION --group-ids $SECURITY_GROUP_ID --query 'SecurityGroups[0].IpPermissions[?FromPort==`8000`]' --output text)
if [ -z "$PORT_8000_EXISTS" ]; then
    echo "Adding port 8000 rule..."
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0
fi

# Check if port 8001 rule exists
PORT_8001_EXISTS=$(aws ec2 describe-security-groups --region $REGION --group-ids $SECURITY_GROUP_ID --query 'SecurityGroups[0].IpPermissions[?FromPort==`8001`]' --output text)
if [ -z "$PORT_8001_EXISTS" ]; then
    echo "Adding port 8001 rule..."
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 8001 \
        --cidr 0.0.0.0/0
fi

echo "Security group configured"

# 8. Create Task Definition 1: SSE (port 8000)
echo "Step 8: Creating task definition - $TASK_FAMILY_SSE..."
aws ecs register-task-definition \
    --region $REGION \
    --family $TASK_FAMILY_SSE \
    --network-mode awsvpc \
    --requires-compatibilities FARGATE \
    --cpu 1024 \
    --memory 3072 \
    --execution-role-arn $EXECUTION_ROLE_ARN \
    --container-definitions '[
        {
            "name": "mcp-container",
            "image": "'$CONTAINER_IMAGE'",
            "essential": true,
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "protocol": "tcp",
                    "name": "mcp-container-8000-tcp",
                    "appProtocol": "http"
                }
            ],
            "environment": [
                {
                    "name": "FMP_API_KEY",
                    "value": "'$FMP_API_KEY'"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$TASK_FAMILY_SSE",
                    "mode": "non-blocking",
                    "awslogs-create-group": "true",
                    "max-buffer-size": "25m",
                    "awslogs-region": "'$REGION'",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]'

echo "Task definition $TASK_FAMILY_SSE:1 created"

# 9. Create Task Definition 2: Streamable HTTP (port 8001)
echo "Step 9: Creating task definition - $TASK_FAMILY_STREAM..."

aws ecs register-task-definition \
    --region $REGION \
    --family $TASK_FAMILY_STREAM \
    --network-mode awsvpc \
    --requires-compatibilities FARGATE \
    --cpu 1024 \
    --memory 3072 \
    --execution-role-arn $EXECUTION_ROLE_ARN \
    --task-role-arn $EXECUTION_ROLE_ARN \
    --container-definitions '[
        {
            "name": "mcp-container-stream",
            "image": "'$CONTAINER_IMAGE'",
            "essential": true,
            "portMappings": [
                {
                    "containerPort": 8001,
                    "hostPort": 8001,
                    "protocol": "tcp",
                    "name": "mcp-container-stream-8001-tcp",
                    "appProtocol": "http"
                }
            ],
            "environment": [
                {
                    "name": "FMP_API_KEY",
                    "value": "'$FMP_API_KEY'"
                },
                {
                    "name": "TRANSPORT",
                    "value": "streamable-http"
                },
                {
                    "name": "PORT",
                    "value": "8001"
                },
                {
                    "name": "STATELESS",
                    "value": "true"
                },
                {
                    "name": "JSON_RESPONSE",
                    "value": "true"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$TASK_FAMILY_STREAM",
                    "mode": "non-blocking",
                    "awslogs-create-group": "true",
                    "max-buffer-size": "25m",
                    "awslogs-region": "'$REGION'",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]'

echo "Task definition $TASK_FAMILY_STREAM:1 created"

# 10. Create ECS Service 1: SSE service
echo "Step 10: Creating ECS service - mcp-task-service-sse..."
SERVICE_NAME_1="mcp-task-service-$(openssl rand -hex 4)"

aws ecs create-service \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME_1 \
    --task-definition $TASK_FAMILY_SSE:1 \
    --desired-count 1 \
    --capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
    --enable-ecs-managed-tags \
    --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},maximumPercent=200,minimumHealthyPercent=100"

echo "Service created: $SERVICE_NAME_1"

# 11. Create ECS Service 2: Streamable HTTP service
echo "Step 11: Creating ECS service - mcp-task-service-stream..."
SERVICE_NAME_2="mcp-task-service-$(openssl rand -hex 4)"

aws ecs create-service \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME_2 \
    --task-definition $TASK_FAMILY_STREAM:1 \
    --desired-count 1 \
    --capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
    --enable-ecs-managed-tags \
    --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},maximumPercent=200,minimumHealthyPercent=100"

echo "Service created: $SERVICE_NAME_2"

# 12. Wait for services to become stable
echo "Step 12: Waiting for services to become stable..."
echo "Waiting for $SERVICE_NAME_1..."
aws ecs wait services-stable --region $REGION --cluster $CLUSTER_NAME --services $SERVICE_NAME_1

echo "Waiting for $SERVICE_NAME_2..."
aws ecs wait services-stable --region $REGION --cluster $CLUSTER_NAME --services $SERVICE_NAME_2

# 13. Get public IPs
echo "Step 13: Getting service endpoints..."

# Get task ARNs
TASK_ARN_1=$(aws ecs list-tasks --region $REGION --cluster $CLUSTER_NAME --service-name $SERVICE_NAME_1 --query 'taskArns[0]' --output text)
TASK_ARN_2=$(aws ecs list-tasks --region $REGION --cluster $CLUSTER_NAME --service-name $SERVICE_NAME_2 --query 'taskArns[0]' --output text)

# Get network interfaces
ENI_1=$(aws ecs describe-tasks --region $REGION --cluster $CLUSTER_NAME --tasks $TASK_ARN_1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
ENI_2=$(aws ecs describe-tasks --region $REGION --cluster $CLUSTER_NAME --tasks $TASK_ARN_2 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)

# Get public IPs
PUBLIC_IP_1=$(aws ec2 describe-network-interfaces --region $REGION --network-interface-ids $ENI_1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
PUBLIC_IP_2=$(aws ec2 describe-network-interfaces --region $REGION --network-interface-ids $ENI_2 --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo ""
echo "Services:"
echo "1. $SERVICE_NAME_1 (SSE):"
echo "   - Endpoint: http://$PUBLIC_IP_1:8000"
echo "   - Transport: SSE"
echo "   - Task Definition: $TASK_FAMILY_SSE:1"
echo ""
echo "2. $SERVICE_NAME_2 (Streamable HTTP):"
echo "   - Endpoint: http://$PUBLIC_IP_2:8001"
echo "   - Transport: streamable-http"
echo "   - Task Definition: $TASK_FAMILY_STREAM:1"
echo ""
echo "Test commands:"
echo "curl http://$PUBLIC_IP_1:8000"
echo "curl http://$PUBLIC_IP_2:8001"
echo ""
echo "Management commands:"
echo "aws ecs list-clusters --region $REGION"
echo "aws ecs list-services --region $REGION --cluster $CLUSTER_NAME"
echo "aws ecs describe-services --region $REGION --cluster $CLUSTER_NAME --services $SERVICE_NAME_1 $SERVICE_NAME_2"
echo ""