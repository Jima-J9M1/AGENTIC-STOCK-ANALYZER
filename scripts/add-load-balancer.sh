#!/bin/bash

# Add Application Load Balancer to existing ECS cluster
# For fmp-mcp-cluster in eu-west-2

set -e

# Configuration
REGION="eu-west-2"
CLUSTER_NAME="fmp-mcp-cluster"
ALB_NAME="mcp-alb"
TARGET_GROUP_NAME="mcp-targets"

echo "=== Adding Application Load Balancer to FMP MCP Cluster ==="
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo "ALB Name: $ALB_NAME"
echo ""

# 1. Get VPC and subnet information
echo "Step 1: Getting VPC configuration..."
VPC_ID=$(aws ec2 describe-vpcs --region $REGION --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
SUBNETS=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text)
SUBNET_ARRAY=($SUBNETS)

echo "VPC: $VPC_ID"
echo "Subnets: ${SUBNET_ARRAY[@]}"

# Need at least 2 subnets in different AZs for ALB
if [ ${#SUBNET_ARRAY[@]} -lt 2 ]; then
    echo "Error: ALB requires at least 2 subnets in different Availability Zones"
    exit 1
fi

# 2. Create security group for ALB
echo "Step 2: Creating security group for ALB..."
ALB_SG_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=mcp-alb-sg" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -z "$ALB_SG_ID" ] || [ "$ALB_SG_ID" = "None" ]; then
    echo "Creating ALB security group..."
    ALB_SG_ID=$(aws ec2 create-security-group \
        --region $REGION \
        --group-name mcp-alb-sg \
        --description "Security group for MCP Application Load Balancer" \
        --vpc-id $VPC_ID \
        --query 'GroupId' \
        --output text)
    
    # Allow HTTP traffic from internet
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $ALB_SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0
    
    # Allow HTTPS traffic from internet
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $ALB_SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0
    
    echo "ALB security group created: $ALB_SG_ID"
else
    echo "ALB security group already exists: $ALB_SG_ID"
fi

# 3. Update ECS security group to allow traffic from ALB
echo "Step 3: Updating ECS security group..."
ECS_SG_ID=$(aws ec2 describe-security-groups --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text)

# Get container port from existing task definition (for security group setup)
CURRENT_SERVICES=$(aws ecs list-services \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --query 'serviceArns' \
    --output text)

if [ -n "$CURRENT_SERVICES" ]; then
    ECS_SERVICE_ARN=$(echo $CURRENT_SERVICES | cut -d' ' -f1)
    ECS_SERVICE_NAME=$(basename $ECS_SERVICE_ARN)
    
    TASK_DEFINITION=$(aws ecs describe-services \
        --region $REGION \
        --cluster $CLUSTER_NAME \
        --services $ECS_SERVICE_NAME \
        --query 'services[0].taskDefinition' \
        --output text)
    
    CONTAINER_PORT=$(aws ecs describe-task-definition \
        --region $REGION \
        --task-definition $TASK_DEFINITION \
        --query 'taskDefinition.containerDefinitions[0].portMappings[0].containerPort' \
        --output text)
    
    echo "Discovered container port: $CONTAINER_PORT"
else
    echo "Error: No ECS services found in cluster $CLUSTER_NAME"
    exit 1
fi

# Check if rule exists
RULE_EXISTS=$(aws ec2 describe-security-groups \
    --region $REGION \
    --group-ids $ECS_SG_ID \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`$CONTAINER_PORT\` && IpProtocol=='tcp' && UserIdGroupPairs[?GroupId=='$ALB_SG_ID']]" \
    --output text)

if [ -z "$RULE_EXISTS" ]; then
    echo "Adding rule to allow ALB traffic to ECS tasks on port $CONTAINER_PORT..."
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $ECS_SG_ID \
        --protocol tcp \
        --port $CONTAINER_PORT \
        --source-group $ALB_SG_ID
else
    echo "ALB to ECS rule already exists"
fi

# 4. Create Application Load Balancer
echo "Step 4: Creating Application Load Balancer..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
    --region $REGION \
    --names $ALB_NAME \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" = "None" ]; then
    echo "Creating ALB: $ALB_NAME"
    ALB_ARN=$(aws elbv2 create-load-balancer \
        --region $REGION \
        --name $ALB_NAME \
        --subnets ${SUBNET_ARRAY[0]} ${SUBNET_ARRAY[1]} \
        --security-groups $ALB_SG_ID \
        --scheme internet-facing \
        --type application \
        --ip-address-type ipv4 \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text)
    
    echo "ALB created: $ALB_ARN"
    
    # Wait for ALB to be active
    echo "Waiting for ALB to become active..."
    aws elbv2 wait load-balancer-available --region $REGION --load-balancer-arns $ALB_ARN
else
    echo "ALB already exists: $ALB_ARN"
fi

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --region $REGION \
    --load-balancer-arns $ALB_ARN \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "ALB DNS Name: $ALB_DNS"

# 5. Create Target Group
echo "Step 5: Creating target group..."
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
    --region $REGION \
    --names $TARGET_GROUP_NAME \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$TARGET_GROUP_ARN" ] || [ "$TARGET_GROUP_ARN" = "None" ]; then
    echo ""
    echo "Choose health check endpoint:"
    echo "1. /health - Dedicated health endpoint (RECOMMENDED)"
    echo "2. /mcp/ - MCP redirect endpoint (legacy compatibility)"
    echo ""
    echo "Note: ALB health checks use GET requests only."
    echo "/health returns HTTP 200, /mcp/ returns HTTP 307 redirect"
    echo ""
    echo -n "Choose option [1-2]: "
    read -r HEALTH_CHOICE
    
    case $HEALTH_CHOICE in
        1)
            HEALTH_PATH="/health"
            HEALTH_MATCHER="HttpCode=200"
            echo "Using dedicated health endpoint: /health (GET → HTTP 200)"
            ;;
        2)
            HEALTH_PATH="/mcp/"
            HEALTH_MATCHER="HttpCode=307"
            echo "Using MCP redirect endpoint: /mcp/ (GET → HTTP 307 redirect)"
            ;;
        *)
            echo "Invalid choice. Using default: /health"
            HEALTH_PATH="/health"
            HEALTH_MATCHER="HttpCode=200"
            ;;
    esac
    
    echo "Creating target group: $TARGET_GROUP_NAME"
    TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
        --region $REGION \
        --name $TARGET_GROUP_NAME \
        --protocol HTTP \
        --port $CONTAINER_PORT \
        --vpc-id $VPC_ID \
        --target-type ip \
        --health-check-enabled \
        --health-check-path $HEALTH_PATH \
        --health-check-protocol HTTP \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --matcher $HEALTH_MATCHER \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    echo "Target group created: $TARGET_GROUP_ARN"
    echo "Health check path: $HEALTH_PATH"
else
    echo "Target group already exists: $TARGET_GROUP_ARN"
    
    # Get current health check path for information
    CURRENT_HEALTH_PATH=$(aws elbv2 describe-target-groups \
        --region $REGION \
        --target-group-arns $TARGET_GROUP_ARN \
        --query 'TargetGroups[0].HealthCheckPath' \
        --output text)
    echo "Current health check path: $CURRENT_HEALTH_PATH"
fi

# 6. Create ALB Listener
echo "Step 6: Creating ALB listener..."
LISTENER_ARN=$(aws elbv2 describe-listeners \
    --region $REGION \
    --load-balancer-arn $ALB_ARN \
    --query 'Listeners[0].ListenerArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$LISTENER_ARN" ] || [ "$LISTENER_ARN" = "None" ]; then
    echo "Creating ALB listener..."
    LISTENER_ARN=$(aws elbv2 create-listener \
        --region $REGION \
        --load-balancer-arn $ALB_ARN \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
        --query 'Listeners[0].ListenerArn' \
        --output text)
    
    echo "Listener created: $LISTENER_ARN"
else
    echo "Listener already exists: $LISTENER_ARN"
fi

# 7. Update ECS service to use target group
echo "Step 7: Updating ECS service with load balancer..."

# Check if service already has a load balancer
CURRENT_LB=$(aws ecs describe-services \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --services $ECS_SERVICE_NAME \
    --query 'services[0].loadBalancers[0].targetGroupArn' \
    --output text)

if [ -n "$CURRENT_LB" ] && [ "$CURRENT_LB" != "None" ]; then
    echo ""
    echo "*** WARNING: Service $ECS_SERVICE_NAME already has a load balancer attached ***"
    echo "Current target group: $CURRENT_LB"
    echo ""
    echo "Options:"
    echo "1. Continue and update load balancer configuration"
    echo "2. Exit (recommended if setup is already working)"
    echo ""
    echo -n "Choose option [1-2]: "
    read -r CHOICE
    
    case $CHOICE in
        1)
            echo "Continuing with load balancer update..."
            ;;
        2)
            echo "Exiting. Your current setup is preserved."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

echo "Using discovered ECS service: $ECS_SERVICE_NAME on port $CONTAINER_PORT"

# Update service with load balancer configuration
aws ecs update-service \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --service $ECS_SERVICE_NAME \
    --load-balancers targetGroupArn=$TARGET_GROUP_ARN,containerName=mcp-container,containerPort=$CONTAINER_PORT \
    --force-new-deployment

echo "ECS service updated with load balancer"

# 8. Wait for service to stabilize
echo "Step 8: Waiting for service to stabilize..."
aws ecs wait services-stable \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --services $ECS_SERVICE_NAME

# 9. Wait for targets to become healthy
echo "Step 9: Waiting for targets to become healthy..."
echo "This may take a few minutes..."

while true; do
    HEALTHY_COUNT=$(aws elbv2 describe-target-health \
        --region $REGION \
        --target-group-arn $TARGET_GROUP_ARN \
        --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
        --output text)
    
    if [ "$HEALTHY_COUNT" -gt 0 ]; then
        echo "Targets are healthy!"
        break
    else
        echo "Waiting for targets to become healthy..."
        sleep 30
    fi
done

echo ""
echo "=== APPLICATION LOAD BALANCER SETUP COMPLETE ==="
echo ""
echo "Load Balancer: $ALB_NAME"
echo "DNS Name: $ALB_DNS"
echo "Target Group: $TARGET_GROUP_NAME"
echo ""
echo "Your service is now accessible at:"
echo "http://$ALB_DNS/mcp/"
echo ""
echo "Test commands:"
echo ""
echo "# Test health endpoint (ALB-compatible GET)"
echo "curl http://$ALB_DNS/health"
echo ""
echo "# Test MCP redirect endpoint (ALB-compatible GET)"
echo "curl http://$ALB_DNS/mcp/"
echo ""
echo "# Test full MCP functionality (JSON-RPC POST)"
echo "curl -L -X POST \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Accept: application/json, text/event-stream\" \\"
echo "  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"ping\",\"params\":{}}' \\"
echo "  http://$ALB_DNS/mcp"
echo ""
echo "Note: DNS propagation may take a few minutes for the ALB name to resolve globally."
echo ""