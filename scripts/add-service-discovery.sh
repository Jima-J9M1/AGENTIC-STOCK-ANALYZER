#!/bin/bash

# Add AWS Cloud Map Service Discovery to existing ECS cluster
# For fmp-mcp-cluster in eu-west-2

set -e

# Configuration
REGION="eu-west-2"
CLUSTER_NAME="fmp-mcp-cluster"
NAMESPACE_NAME="fmp-mcp-services"
SERVICE_NAME="mcp-streamable"

echo "=== Adding Service Discovery to FMP MCP Cluster ==="
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE_NAME"
echo ""

# 1. Create Cloud Map namespace
echo "Step 1: Creating Cloud Map namespace..."
NAMESPACE_ID=$(aws servicediscovery list-namespaces \
    --region $REGION \
    --filters Name=TYPE,Values=DNS_PRIVATE \
    --query "Namespaces[?Name=='$NAMESPACE_NAME'].Id" \
    --output text)

if [ -z "$NAMESPACE_ID" ] || [ "$NAMESPACE_ID" = "None" ]; then
    echo "Creating new namespace: $NAMESPACE_NAME"
    
    # Get VPC ID
    VPC_ID=$(aws ec2 describe-vpcs --region $REGION --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
    
    NAMESPACE_ID=$(aws servicediscovery create-private-dns-namespace \
        --region $REGION \
        --name $NAMESPACE_NAME \
        --vpc $VPC_ID \
        --description "Service discovery for FMP MCP services" \
        --query 'OperationId' \
        --output text)
    
    echo "Namespace creation initiated. Operation ID: $NAMESPACE_ID"
    echo "Waiting for namespace creation to complete..."
    
    # Wait for operation to complete
    while true; do
        STATUS=$(aws servicediscovery get-operation \
            --region $REGION \
            --operation-id $NAMESPACE_ID \
            --query 'Operation.Status' \
            --output text)
        
        if [ "$STATUS" = "SUCCESS" ]; then
            NAMESPACE_ID=$(aws servicediscovery get-operation \
                --region $REGION \
                --operation-id $NAMESPACE_ID \
                --query 'Operation.Targets.NAMESPACE' \
                --output text)
            echo "Namespace created successfully: $NAMESPACE_ID"
            break
        elif [ "$STATUS" = "FAIL" ]; then
            echo "Namespace creation failed"
            exit 1
        else
            echo "Status: $STATUS, waiting..."
            sleep 10
        fi
    done
else
    echo "Namespace already exists: $NAMESPACE_ID"
fi

# 2. Create service in Cloud Map
echo "Step 2: Creating Cloud Map service..."
DISCOVERY_SERVICE_ID=$(aws servicediscovery list-services \
    --region $REGION \
    --filters Name=NAMESPACE_ID,Values=$NAMESPACE_ID \
    --query "Services[?Name=='$SERVICE_NAME'].Id" \
    --output text)

if [ -z "$DISCOVERY_SERVICE_ID" ] || [ "$DISCOVERY_SERVICE_ID" = "None" ]; then
    echo "Creating Cloud Map service: $SERVICE_NAME"
    
    DISCOVERY_SERVICE_ID=$(aws servicediscovery create-service \
        --region $REGION \
        --name $SERVICE_NAME \
        --namespace-id $NAMESPACE_ID \
        --dns-config NamespaceId=$NAMESPACE_ID,DnsRecords=[{Type=A,TTL=60}],RoutingPolicy=MULTIVALUE \
        --health-check-custom-config FailureThreshold=1 \
        --description "MCP Streamable HTTP service" \
        --query 'Service.Id' \
        --output text)
    
    echo "Cloud Map service created: $DISCOVERY_SERVICE_ID"
else
    echo "Cloud Map service already exists: $DISCOVERY_SERVICE_ID"
fi

# 3. Get current ECS service details
echo "Step 3: Getting current ECS service configuration..."
CURRENT_SERVICES=$(aws ecs list-services \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --query 'serviceArns' \
    --output text)

if [ -z "$CURRENT_SERVICES" ]; then
    echo "No ECS services found in cluster $CLUSTER_NAME"
    exit 1
fi

# Get the first service (assuming it's the MCP service)
ECS_SERVICE_ARN=$(echo $CURRENT_SERVICES | cut -d' ' -f1)
ECS_SERVICE_NAME=$(basename $ECS_SERVICE_ARN)

echo "Found ECS service: $ECS_SERVICE_NAME"

# Get current service configuration
CURRENT_CONFIG=$(aws ecs describe-services \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --services $ECS_SERVICE_NAME)

TASK_DEFINITION=$(echo $CURRENT_CONFIG | jq -r '.services[0].taskDefinition')
DESIRED_COUNT=$(echo $CURRENT_CONFIG | jq -r '.services[0].desiredCount')
NETWORK_CONFIG=$(echo $CURRENT_CONFIG | jq -r '.services[0].networkConfiguration')

echo "Current task definition: $TASK_DEFINITION"
echo "Desired count: $DESIRED_COUNT"

# 4. Update ECS service with service discovery
echo "Step 4: Updating ECS service with service discovery..."

# Create service registry configuration
SERVICE_REGISTRIES='[
    {
        "registryArn": "arn:aws:servicediscovery:'$REGION':612768032820:service/'$DISCOVERY_SERVICE_ID'",
        "containerName": "mcp-container"
    }
]'

# Update the service
aws ecs update-service \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --service $ECS_SERVICE_NAME \
    --service-registries "$SERVICE_REGISTRIES" \
    --force-new-deployment

echo "ECS service updated with service discovery"

# 5. Wait for service to stabilize
echo "Step 5: Waiting for service to stabilize..."
aws ecs wait services-stable \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --services $ECS_SERVICE_NAME

echo ""
echo "=== SERVICE DISCOVERY SETUP COMPLETE ==="
echo ""
echo "Namespace: $NAMESPACE_NAME ($NAMESPACE_ID)"
echo "Service: $SERVICE_NAME ($DISCOVERY_SERVICE_ID)"
echo "DNS Name: $SERVICE_NAME.$NAMESPACE_NAME"
echo ""
echo "Your service can now be reached at:"
echo "- Internal DNS: $SERVICE_NAME.$NAMESPACE_NAME"
echo "- From within the VPC: http://$SERVICE_NAME.$NAMESPACE_NAME:8000"
echo ""
echo "Test from another ECS task or EC2 instance in the same VPC:"
echo "curl http://$SERVICE_NAME.$NAMESPACE_NAME:8000/mcp/meta"
echo ""
echo "To list all registered instances:"
echo "aws servicediscovery list-instances --region $REGION --service-id $DISCOVERY_SERVICE_ID"
echo ""