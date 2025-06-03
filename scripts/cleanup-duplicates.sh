#!/bin/bash

# Cleanup Duplicate ECS Resources
# For fmp-mcp-cluster

set -e

REGION="eu-west-2"
CLUSTER_NAME="fmp-mcp-cluster"

echo "=== ECS Duplicate Resource Cleanup ==="
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo ""

# 1. List all services
echo "Step 1: Checking for duplicate services..."
SERVICES=$(aws ecs list-services \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --query 'serviceArns' \
    --output text)

if [ -z "$SERVICES" ]; then
    echo "No services found in cluster."
    exit 0
fi

echo "Found services:"
aws ecs describe-services \
    --region $REGION \
    --cluster $CLUSTER_NAME \
    --services $SERVICES \
    --query 'services[*].{Name:serviceName,Status:status,Desired:desiredCount,Running:runningCount,HasLB:length(loadBalancers),TaskDef:taskDefinition,CreatedAt:createdAt}' \
    --output table

# Check for duplicate task definitions
echo ""
echo "Checking for duplicate task definitions..."
declare -A TASK_FAMILIES
DUPLICATES_FOUND=false

for SERVICE_ARN in $SERVICES; do
    SERVICE_NAME=$(basename $SERVICE_ARN)
    TASK_DEF=$(aws ecs describe-services \
        --region $REGION \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --query 'services[0].taskDefinition' \
        --output text)
    
    # Extract task family (without revision)
    FAMILY=$(echo $TASK_DEF | cut -d':' -f6 | cut -d'/' -f2)
    
    if [ -n "${TASK_FAMILIES[$FAMILY]}" ]; then
        echo "🔄 DUPLICATE: Services '${TASK_FAMILIES[$FAMILY]}' and '$SERVICE_NAME' both use task family '$FAMILY'"
        DUPLICATES_FOUND=true
    else
        TASK_FAMILIES[$FAMILY]=$SERVICE_NAME
    fi
done

if [ "$DUPLICATES_FOUND" = false ]; then
    echo "✅ No duplicate task definitions found"
fi

echo ""

# Count services
SERVICE_COUNT=$(echo $SERVICES | wc -w)
if [ $SERVICE_COUNT -gt 1 ]; then
    echo "*** Found $SERVICE_COUNT services - you probably only need 1 ***"
    echo ""
    echo "Recommended cleanup strategy:"
    echo "1. Keep the service WITH load balancer attached"
    echo "2. Delete services WITHOUT load balancer"
    echo "3. Scale the kept service to desired count (e.g., 2)"
    echo ""
    
    # Show which services have load balancers
    echo "Services with load balancers:"
    for SERVICE_ARN in $SERVICES; do
        SERVICE_NAME=$(basename $SERVICE_ARN)
        HAS_LB=$(aws ecs describe-services \
            --region $REGION \
            --cluster $CLUSTER_NAME \
            --services $SERVICE_NAME \
            --query 'services[0].loadBalancers | length(@)' \
            --output text)
        
        if [ "$HAS_LB" -gt 0 ]; then
            echo "  ✅ $SERVICE_NAME (KEEP THIS ONE)"
        else
            echo "  ❌ $SERVICE_NAME (consider deleting)"
        fi
    done
    
    echo ""
    echo "Do you want to automatically cleanup duplicate services? [y/N]"
    read -r CONFIRM
    
    if [[ $CONFIRM =~ ^[Yy]$ ]]; then
        echo "Starting cleanup..."
        
        # Delete services without load balancers
        for SERVICE_ARN in $SERVICES; do
            SERVICE_NAME=$(basename $SERVICE_ARN)
            HAS_LB=$(aws ecs describe-services \
                --region $REGION \
                --cluster $CLUSTER_NAME \
                --services $SERVICE_NAME \
                --query 'services[0].loadBalancers | length(@)' \
                --output text)
            
            if [ "$HAS_LB" -eq 0 ]; then
                echo "Scaling down and deleting service: $SERVICE_NAME"
                
                # Scale to 0
                aws ecs update-service \
                    --region $REGION \
                    --cluster $CLUSTER_NAME \
                    --service $SERVICE_NAME \
                    --desired-count 0 >/dev/null
                
                # Wait a moment
                sleep 5
                
                # Delete service
                aws ecs delete-service \
                    --region $REGION \
                    --cluster $CLUSTER_NAME \
                    --service $SERVICE_NAME >/dev/null
                
                echo "  ✅ Deleted $SERVICE_NAME"
            fi
        done
        
        echo ""
        echo "Cleanup complete! Remaining services:"
        REMAINING_SERVICES=$(aws ecs list-services \
            --region $REGION \
            --cluster $CLUSTER_NAME \
            --query 'serviceArns' \
            --output text)
        
        if [ -n "$REMAINING_SERVICES" ]; then
            aws ecs describe-services \
                --region $REGION \
                --cluster $CLUSTER_NAME \
                --services $REMAINING_SERVICES \
                --query 'services[*].{Name:serviceName,Status:status,Desired:desiredCount,Running:runningCount}' \
                --output table
        fi
        
    else
        echo "Cleanup cancelled. Manual commands to delete services:"
        for SERVICE_ARN in $SERVICES; do
            SERVICE_NAME=$(basename $SERVICE_ARN)
            HAS_LB=$(aws ecs describe-services \
                --region $REGION \
                --cluster $CLUSTER_NAME \
                --services $SERVICE_NAME \
                --query 'services[0].loadBalancers | length(@)' \
                --output text)
            
            if [ "$HAS_LB" -eq 0 ]; then
                echo "aws ecs update-service --region $REGION --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count 0"
                echo "aws ecs delete-service --region $REGION --cluster $CLUSTER_NAME --service $SERVICE_NAME"
            fi
        done
    fi
else
    echo "✅ Only 1 service found - no cleanup needed"
fi

echo ""
echo "=== Cleanup Complete ==="