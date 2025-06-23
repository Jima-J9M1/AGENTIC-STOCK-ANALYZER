#!/bin/bash
# ALB Lifecycle Management Script for FMP MCP

set -e

TERRAFORM_DIR="/home/ctait/git/fmp-mcp-server/terraform/fmp-mcp-modular"
cd "$TERRAFORM_DIR"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}⚖️ FMP MCP ALB Lifecycle Manager${NC}"
echo "=================================================="

# Function to check current ALB status
check_alb_status() {
    echo -e "${CYAN}📊 Current ALB Status:${NC}"
    echo ""
    
    local alb_regions=("eu-west-1" "eu-west-2" "us-east-1")
    local total_albs=0
    local total_cost=0
    
    for region in "${alb_regions[@]}"; do
        echo -n "├── $region: "
        
        # Check for ALBs in region
        local alb_count=$(aws elbv2 describe-load-balancers \
            --region "$region" \
            --query 'LoadBalancers[?contains(LoadBalancerName, `fmp-mcp`)]' \
            --output text 2>/dev/null | wc -l || echo "0")
        
        if [ "$alb_count" -gt 0 ]; then
            # Get ALB details
            local alb_dns=$(aws elbv2 describe-load-balancers \
                --region "$region" \
                --query 'LoadBalancers[?contains(LoadBalancerName, `fmp-mcp`)].DNSName' \
                --output text 2>/dev/null || echo "")
            
            local alb_state=$(aws elbv2 describe-load-balancers \
                --region "$region" \
                --query 'LoadBalancers[?contains(LoadBalancerName, `fmp-mcp`)].State.Code' \
                --output text 2>/dev/null || echo "unknown")
            
            echo -e "${GREEN}✅ Active ($alb_state)${NC}"
            [ -n "$alb_dns" ] && echo "    DNS: $alb_dns"
            
            total_albs=$((total_albs + 1))
            # ALB cost varies by region
            if [ "$region" = "us-east-1" ]; then
                total_cost=$(echo "$total_cost + 16.20" | bc)
            else
                total_cost=$(echo "$total_cost + 16.43" | bc)
            fi
        else
            echo -e "${RED}❌ Not found${NC}"
        fi
    done
    
    echo ""
    echo -e "${YELLOW}💰 ALB Cost Summary:${NC}"
    echo "├── Active ALBs: $total_albs/3"
    echo "├── Monthly cost: \$$(printf "%.2f" $total_cost)"
    echo "└── Annual cost: \$$(printf "%.2f" $(echo "$total_cost * 12" | bc))"
}

# Function to check ECS task status
check_ecs_status() {
    echo -e "${CYAN}🐳 Current ECS Status:${NC}"
    echo ""
    
    local regions=("eu-west-1:fmp-mcp-cluster:fmp-mcp-dev-service" 
                   "eu-west-2:fmp-mcp-eu-west-2-cluster:fmp-mcp-dev-eu-west-2-service"
                   "us-east-1:fmp-mcp-us-east-1-cluster:fmp-mcp-dev-us-east-1-service")
    
    local total_tasks=0
    
    for region_info in "${regions[@]}"; do
        IFS=':' read -r region cluster service <<< "$region_info"
        echo -n "├── $region: "
        
        if tasks=$(aws ecs describe-services --cluster "$cluster" --services "$service" --region "$region" --query 'services[0].runningCount' --output text 2>/dev/null); then
            if [ "$tasks" -gt 0 ]; then
                echo -e "${GREEN}$tasks tasks running${NC}"
            else
                echo -e "${YELLOW}$tasks tasks (scaled down)${NC}"
            fi
            total_tasks=$((total_tasks + tasks))
        else
            echo -e "${RED}Service not found${NC}"
        fi
    done
    
    echo ""
    echo "└── Total running tasks: $total_tasks"
}

# Function to create ALBs (weekend start)
create_albs() {
    echo -e "${GREEN}🚀 Creating ALBs for weekend period...${NC}"
    
    export PATH="$HOME/.local/bin:$PATH"
    
    echo "Step 1: Enabling weekend mode with ALB creation..."
    terraform apply \
        -var="enable_weekend_only=true" \
        -var="destroy_albs_when_scaled_down=false" \
        -auto-approve
    
    echo "Step 2: Scaling eu-west-2 to active state..."
    terraform apply \
        -var="desired_count=2" \
        -target="module.fmp_mcp_eu_west_2[0].aws_ecs_service.main" \
        -auto-approve
    
    echo -e "${GREEN}✅ ALBs created and eu-west-2 scaled up${NC}"
    echo "⏳ Waiting for ALBs to become fully operational..."
    sleep 60
    
    # Test ALB health
    test_alb_connectivity
}

# Function to destroy ALBs (weekend end)
destroy_albs() {
    echo -e "${YELLOW}💥 Destroying ALBs for maximum cost savings...${NC}"
    
    export PATH="$HOME/.local/bin:$PATH"
    
    echo "Step 1: Scaling all tasks to 0..."
    terraform apply -var="desired_count=0" -auto-approve
    
    echo "Step 2: Enabling weekend mode with ALB destruction..."
    terraform apply \
        -var="enable_weekend_only=true" \
        -var="destroy_albs_when_scaled_down=true" \
        -auto-approve
    
    echo -e "${GREEN}✅ All tasks scaled down and ALBs destroyed${NC}"
    
    # Verify ALBs are gone
    echo "⏳ Verifying ALB destruction..."
    sleep 30
    check_alb_status
}

# Function to test ALB connectivity
test_alb_connectivity() {
    echo -e "${CYAN}🔍 Testing ALB Connectivity:${NC}"
    echo ""
    
    local alb_regions=("eu-west-1" "eu-west-2" "us-east-1")
    
    for region in "${alb_regions[@]}"; do
        echo -n "├── Testing $region ALB: "
        
        local alb_dns=$(aws elbv2 describe-load-balancers \
            --region "$region" \
            --query 'LoadBalancers[?contains(LoadBalancerName, `fmp-mcp`)].DNSName' \
            --output text 2>/dev/null || echo "")
        
        if [ -n "$alb_dns" ]; then
            # Test health endpoint with timeout
            if timeout 10 curl -f -s "http://$alb_dns/health" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Accessible${NC}"
            else
                echo -e "${YELLOW}⏳ Not ready yet${NC}"
            fi
        else
            echo -e "${RED}❌ No ALB found${NC}"
        fi
    done
}

# Function to show cost comparison
show_cost_comparison() {
    echo -e "${BLUE}💰 ALB Management Cost Comparison:${NC}"
    echo ""
    
    echo -e "${YELLOW}Scenario 1: Keep ALBs Running (Current Weekend Mode)${NC}"
    echo "├── Active time: 32 hours/week (Sat-Sun 6AM-10PM)"
    echo "├── Fargate costs: ~\$15/month (weekend only)"
    echo "├── ALB costs: ~\$49/month (always running)"
    echo "├── Other services: ~\$3/month"
    echo "└── Total: ~\$67/month (\$804/year)"
    echo ""
    
    echo -e "${GREEN}Scenario 2: Destroy ALBs During Week (Maximum Savings)${NC}"
    echo "├── Active time: 32 hours/week (Sat-Sun 6AM-10PM)" 
    echo "├── Fargate costs: ~\$15/month (weekend only)"
    echo "├── ALB costs: ~\$7/month (weekend only)"
    echo "├── Other services: ~\$3/month"
    echo "└── Total: ~\$25/month (\$300/year)"
    echo ""
    
    echo -e "${CYAN}💾 Additional Savings with ALB Destruction:${NC}"
    echo "├── Monthly savings: ~\$42/month"
    echo "├── Annual savings: ~\$504/year"
    echo "└── Total savings vs 24/7: ~\$260/month (91% reduction)"
    echo ""
    
    echo -e "${YELLOW}⚠️ Trade-offs:${NC}"
    echo "├── ALB creation time: 5-10 minutes"
    echo "├── DNS propagation: 1-2 minutes"
    echo "└── Total startup time: 6-12 minutes on weekends"
}

# Function to estimate weekend startup time
estimate_startup_time() {
    echo -e "${CYAN}⏱️ Weekend Startup Time Estimation:${NC}"
    echo ""
    echo "When ALBs are destroyed, weekend startup involves:"
    echo "├── 1. ALB creation: 5-8 minutes"
    echo "├── 2. Target group health checks: 2-3 minutes"
    echo "├── 3. ECS task startup: 2-3 minutes"
    echo "├── 4. DNS propagation: 1-2 minutes"
    echo "└── Total: 10-16 minutes for full availability"
    echo ""
    echo "💡 Recommendation: Start weekend period at 5:50 AM"
    echo "   to ensure full availability by 6:00 AM"
}

# Function to schedule optimized timing
show_optimized_schedule() {
    echo -e "${BLUE}⏰ Optimized Weekend Schedule:${NC}"
    echo ""
    echo "🚀 Weekend Start (Saturday):"
    echo "├── 05:50 AM UTC: Start ALB creation"
    echo "├── 05:55 AM UTC: Start ECS scaling"
    echo "└── 06:00 AM UTC: Full service available"
    echo ""
    echo "⏸️ Weekend End (Sunday):"
    echo "├── 22:00 PM UTC: Scale down ECS tasks"
    echo "├── 22:05 PM UTC: Destroy ALBs"
    echo "└── 22:10 PM UTC: Full shutdown complete"
    echo ""
    echo "💡 Cron jobs for optimized timing:"
    echo "50 5 * * 6 /path/to/alb-manager.sh create-albs"
    echo "0 22 * * 0 /path/to/alb-manager.sh destroy-albs"
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}Choose an action:${NC}"
    echo "1. Check current ALB and ECS status"
    echo "2. Create ALBs and scale up (weekend start)"
    echo "3. Scale down and destroy ALBs (weekend end)"
    echo "4. Test ALB connectivity"
    echo "5. Show cost comparison (keep vs destroy ALBs)"
    echo "6. Show optimized weekend schedule"
    echo "7. Estimate weekend startup time"
    echo "8. Exit"
    echo ""
    echo -n "Enter your choice [1-8]: "
}

# Handle command line arguments
if [[ $# -gt 0 ]]; then
    case "$1" in
        "create-albs")
            create_albs
            exit 0
            ;;
        "destroy-albs")
            destroy_albs
            exit 0
            ;;
        "status")
            check_alb_status
            check_ecs_status
            exit 0
            ;;
        "test-connectivity")
            test_alb_connectivity
            exit 0
            ;;
    esac
fi

# Interactive mode
while true; do
    show_menu
    read choice
    
    case $choice in
        1)
            check_alb_status
            echo ""
            check_ecs_status
            ;;
        2)
            create_albs
            ;;
        3)
            destroy_albs
            ;;
        4)
            test_alb_connectivity
            ;;
        5)
            show_cost_comparison
            ;;
        6)
            show_optimized_schedule
            ;;
        7)
            estimate_startup_time
            ;;
        8)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option. Please choose 1-8.${NC}"
            ;;
    esac
    echo ""
    echo "Press Enter to continue..."
    read
done