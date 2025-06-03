#!/bin/bash

# ECS FMP MCP Server Setup Script
# Sets up a streamable HTTP MCP Server on AWS ECS Fargate

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

if [ -z "$TASK_FAMILY" ]; then
    echo "TASK_FAMILY not found in environment."
    echo -n "Please enter task definition family name (e.g., mcp-task-stream): "
    read -r TASK_FAMILY
    if [ -z "$TASK_FAMILY" ]; then
        echo "Error: TASK_FAMILY cannot be empty"
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

if [ -z "$PORT" ]; then
    echo "PORT not found in environment."
    echo -n "Please enter port number (e.g., 8000, 8001): "
    read -r PORT
    if [ -z "$PORT" ]; then
        echo "Error: PORT cannot be empty"
        exit 1
    fi
fi

echo "=== FMP MCP Server ECS Setup ==="
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo "Task Family: $TASK_FAMILY"
echo "Container Image: $CONTAINER_IMAGE"
echo "Port: $PORT"
echo "FMP API Key: ${FMP_API_KEY:0:8}... (truncated for security)"
echo ""

# 1. Install/Update AWS CLI v2
#echo "Step 1: Installing AWS CLI v2..."
#sudo yum remove awscli -y || true
#curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
#unzip awscliv2.zip
#sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update
#rm -rf awscliv2.zip aws/

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
echo "   - SecretsManagerReadWrite"
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
    
    # Attach ECS execution policy
    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
        
    # Attach Secrets Manager policy
    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
        
    # Attach CloudWatch Logs policy
    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
    
    EXECUTION_ROLE_ARN=$(aws iam get-role --role-name ecsTaskExecutionRole --query 'Role.Arn' --output text)
    echo "Created execution role: $EXECUTION_ROLE_ARN"
else
    echo "Execution role exists: $EXECUTION_ROLE_ARN"
    
    # Check if SecretsManagerReadWrite policy is attached
    SECRETS_POLICY_ATTACHED=$(aws iam list-attached-role-policies --role-name ecsTaskExecutionRole --query "AttachedPolicies[?PolicyName=='SecretsManagerReadWrite'].PolicyArn" --output text)
    
    if [ -z "$SECRETS_POLICY_ATTACHED" ]; then
        echo "Attaching SecretsManagerReadWrite policy to ecsTaskExecutionRole..."
        aws iam attach-role-policy \
            --role-name ecsTaskExecutionRole \
            --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
    fi
    
    # Check if CloudWatchLogsFullAccess policy is attached
    LOGS_POLICY_ATTACHED=$(aws iam list-attached-role-policies --role-name ecsTaskExecutionRole --query "AttachedPolicies[?PolicyName=='CloudWatchLogsFullAccess'].PolicyArn" --output text)
    
    if [ -z "$LOGS_POLICY_ATTACHED" ]; then
        echo "Attaching CloudWatchLogsFullAccess policy to ecsTaskExecutionRole..."
        aws iam attach-role-policy \
            --role-name ecsTaskExecutionRole \
            --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
    fi
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

# Check if port rule exists
PORT_EXISTS=$(aws ec2 describe-security-groups --region $REGION --group-ids $SECURITY_GROUP_ID --query "SecurityGroups[0].IpPermissions[?FromPort==\`$PORT\`]" --output text)
if [ -z "$PORT_EXISTS" ]; then
    echo "Adding port $PORT rule..."
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port $PORT \
        --cidr 0.0.0.0/0
fi

echo "Security group configured"

# 8. Store API key in AWS Secrets Manager
echo "Step 8: Storing API key in AWS Secrets Manager..."
SECRET_NAME="fmp-mcp-api-key"

# Check if secret exists
SECRET_EXISTS=$(aws secretsmanager list-secrets --region $REGION --query "SecretList[?Name==\`$SECRET_NAME\`].ARN" --output text)

if [ -z "$SECRET_EXISTS" ]; then
    echo "Creating new secret: $SECRET_NAME"
    SECRET_ARN=$(aws secretsmanager create-secret \
        --region $REGION \
        --name $SECRET_NAME \
        --secret-string "{\"FMP_API_KEY\":\"$FMP_API_KEY\"}" \
        --query ARN --output text)
else
    echo "Updating existing secret: $SECRET_NAME"
    aws secretsmanager update-secret \
        --region $REGION \
        --secret-id $SECRET_NAME \
        --secret-string "{\"FMP_API_KEY\":\"$FMP_API_KEY\"}"
    SECRET_ARN=$SECRET_EXISTS
fi

echo "Secret stored: $SECRET_ARN"

# 9. Create Task Definition for Streamable HTTP
echo "Step 9: Creating task definition - $TASK_FAMILY..."

aws ecs register-task-definition \
    --region $REGION \
    --family $TASK_FAMILY \
    --network-mode awsvpc \
    --requires-compatibilities FARGATE \
    --cpu 1024 \
    --memory 3072 \
    --execution-role-arn $EXECUTION_ROLE_ARN \
    --task-role-arn $EXECUTION_ROLE_ARN \
    --container-definitions '[
        {
            "name": "mcp-container",
            "image": "'$CONTAINER_IMAGE'",
            "essential": true,
            "portMappings": [
                {
                    "containerPort": '$PORT',
                    "hostPort": '$PORT',
                    "protocol": "tcp",
                    "name": "mcp-container-'$PORT'-tcp",
                    "appProtocol": "http"
                }
            ],
            "environment": [
                {
                    "name": "TRANSPORT",
                    "value": "streamable-http"
                },
                {
                    "name": "PORT",
                    "value": "'$PORT'"
                },
                {
                    "name": "STATELESS",
                    "value": "true"
                }
            ],
            "secrets": [
                {
                    "name": "FMP_API_KEY",
                    "valueFrom": "'$SECRET_ARN':FMP_API_KEY::"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/'$TASK_FAMILY'",
                    "mode": "non-blocking",
                    "awslogs-create-group": "true",
                    "max-buffer-size": "25m",
                    "awslogs-region": "'$REGION'",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]'

echo "Task definition $TASK_FAMILY:1 created"

# 10. Create ECS Service for Streamable HTTP
echo "Step 10: Creating ECS service - mcp-streamable-service..."

# Check for existing services
EXISTING_SERVICES=$(aws ecs list-services \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --query 'serviceArns' \
    --output text)

if [ -n "$EXISTING_SERVICES" ]; then
    echo ""
    echo "*** WARNING: Found existing services in cluster $CLUSTER_NAME ***"
    
    # Check for services using the same task definition
    SAME_TASKDEF_SERVICE=""
    for SERVICE_ARN in $EXISTING_SERVICES; do
        SERVICE_NAME=$(basename $SERVICE_ARN)
        CURRENT_TASKDEF=$(aws ecs describe-services \
            --region $REGION \
            --cluster $CLUSTER_NAME \
            --services $SERVICE_NAME \
            --query 'services[0].taskDefinition' \
            --output text)
        
        # Extract just the family name (without revision)
        CURRENT_FAMILY=$(echo $CURRENT_TASKDEF | cut -d':' -f6 | cut -d'/' -f2)
        
        if [[ "$CURRENT_FAMILY" == "$TASK_FAMILY"* ]]; then
            SAME_TASKDEF_SERVICE=$SERVICE_NAME
            echo "🔄 DUPLICATE DETECTED: Service '$SERVICE_NAME' already uses task family '$TASK_FAMILY'"
            break
        fi
    done
    
    aws ecs describe-services \
        --region $REGION \
        --cluster $CLUSTER_NAME \
        --services $EXISTING_SERVICES \
        --query 'services[*].{Name:serviceName,Status:status,Desired:desiredCount,Running:runningCount,TaskDef:taskDefinition}' \
        --output table
    
    if [ -n "$SAME_TASKDEF_SERVICE" ]; then
        echo ""
        echo "🚨 DUPLICATE SERVICE DETECTED! 🚨"
        echo "Service '$SAME_TASKDEF_SERVICE' already runs the same task definition family '$TASK_FAMILY'"
        echo ""
        echo "Recommended actions:"
        echo "1. Update existing service '$SAME_TASKDEF_SERVICE' (RECOMMENDED)"
        echo "2. Create new service anyway (will cause duplicates and extra costs)"
        echo "3. Exit and cleanup manually"
    else
        echo ""
        echo "No duplicate task definitions found."
        echo "Options:"
        echo "1. Create new service"
        echo "2. Update existing service"
        echo "3. Exit and cleanup manually"
    fi
    echo ""
    echo -n "Choose option [1-3]: "
    
    case $CHOICE in
        1)
            echo "Creating new service..."
            SERVICE_NAME="mcp-streamable-service-$(openssl rand -hex 4)"
            ;;
        2)
            # Use the service with same task definition if found, otherwise first service
            if [ -n "$SAME_TASKDEF_SERVICE" ]; then
                SERVICE_NAME=$SAME_TASKDEF_SERVICE
            else
                EXISTING_SERVICE_ARN=$(echo $EXISTING_SERVICES | cut -d' ' -f1)
                SERVICE_NAME=$(basename $EXISTING_SERVICE_ARN)
            fi
            echo "Will update existing service: $SERVICE_NAME"
            SKIP_SERVICE_CREATION=true
            ;;
        3)
            echo "Exiting. Please cleanup existing services first."
            echo "To delete a service: aws ecs delete-service --region $REGION --cluster $CLUSTER_NAME --service <service-name>"
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
else
    SERVICE_NAME="mcp-streamable-service-$(openssl rand -hex 4)"
fi

if [ "$SKIP_SERVICE_CREATION" != "true" ]; then
    aws ecs create-service \
        --region $REGION \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_FAMILY:1 \
        --desired-count 1 \
        --capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
        --enable-ecs-managed-tags \
        --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},maximumPercent=200,minimumHealthyPercent=100"
    
    echo "Service created: $SERVICE_NAME"
else
    echo "Updating existing service: $SERVICE_NAME"
    aws ecs update-service \
        --region $REGION \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_FAMILY:1 \
        --force-new-deployment
    
    echo "Service updated: $SERVICE_NAME"
fi

# 11. Wait for service to become stable
echo "Step 11: Waiting for service to become stable..."
echo "Waiting for $SERVICE_NAME..."
aws ecs wait services-stable --region $REGION --cluster $CLUSTER_NAME --services $SERVICE_NAME

# 12. Get public IP
echo "Step 12: Getting service endpoint..."

# Get task ARN
TASK_ARN=$(aws ecs list-tasks --region $REGION --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --query 'taskArns[0]' --output text)

# Get network interface
ENI=$(aws ecs describe-tasks --region $REGION --cluster $CLUSTER_NAME --tasks $TASK_ARN --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)

# Get public IP
PUBLIC_IP=$(aws ec2 describe-network-interfaces --region $REGION --network-interface-ids $ENI --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo ""
echo "Service: $SERVICE_NAME"
echo "- Endpoint: http://$PUBLIC_IP:$PORT/mcp/"
echo "- Transport: streamable-http (stateless)"
echo "- Task Definition: $TASK_FAMILY:1"
echo ""
echo "Test command:"
echo "curl http://$PUBLIC_IP:$PORT/mcp/meta"
echo ""
echo "MCP Inspector Connection URL:"
echo "http://$PUBLIC_IP:$PORT/mcp/"
echo ""
echo "Management commands:"
echo "aws ecs list-clusters --region $REGION"
echo "aws ecs list-services --region $REGION --cluster $CLUSTER_NAME"
echo "aws ecs describe-services --region $REGION --cluster $CLUSTER_NAME --services $SERVICE_NAME"
echo ""