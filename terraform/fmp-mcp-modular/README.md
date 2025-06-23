# MCP Server - AWS Infrastructure

This Terraform configuration creates a production-ready AWS infrastructure for containerized MCP (Model Context Protocol) server deployments. It features single-region deployment with optional multi-region support via deployment scripts.

## 🏗️ Architecture Overview

The infrastructure is designed as a modern, scalable, and cost-optimized container platform with optional weekend-only scheduling for cost savings.

## 📦 Infrastructure Components

Each AWS region deployment creates the following complete set of resources:

### **Compute & Container Infrastructure (4 resources)**
- **1 ECS Cluster** - Container orchestration platform (`aws_ecs_cluster`)
- **1 ECS Service** - Manages task lifecycle and scaling (`aws_ecs_service`)
- **1 Task Definition** - Container blueprint with CPU/memory specifications (`aws_ecs_task_definition`)
- **2 ECS Tasks** - Running container instances (default `desired_count=2`)

### **Load Balancing & Traffic Management (3 resources)**
- **1 Application Load Balancer (ALB)** - Public-facing traffic distribution (`aws_lb`)
- **1 Target Group** - Routes traffic to healthy ECS tasks (`aws_lb_target_group`)
- **1 ALB Listener** - Handles incoming traffic on port 80 (`aws_lb_listener`)

### **Networking Infrastructure (7 resources)**
- **1 Dedicated VPC** - Isolated network environment (`aws_vpc`)
- **3 Public Subnets** - High availability across multiple AZs (`aws_subnet`)
- **1 Internet Gateway** - Internet access for VPC (`aws_internet_gateway`)
- **1 Route Table** - Routes traffic to/from internet (`aws_route_table`)
- **3 Route Table Associations** - Connect subnets to routing (`aws_route_table_association`)

### **Security (2 resources)**
- **1 ALB Security Group** - Controls inbound traffic (ports 80/443) (`aws_security_group`)
- **1 ECS Tasks Security Group** - Controls container access (port 8001 from ALB only) (`aws_security_group`)

### **Service Discovery (2 resources, if enabled)**
- **1 Service Discovery Namespace** - Private DNS namespace (`aws_service_discovery_private_dns_namespace`)
- **1 Service Discovery Service** - Service registration and health checks (`aws_service_discovery_service`)

### **Monitoring & Logging (1 resource)**
- **1 CloudWatch Log Group** - Centralized container logging (`aws_cloudwatch_log_group`)

### **Security & Secrets (3 resources)**
- **2 IAM Roles** - ECS execution and task roles (`aws_iam_role`)
- **1 Secrets Manager Secret** - Secure API key storage (`aws_secretsmanager_secret`)

**Total Resources per Region: 19-21 resources**

## 🏛️ Architecture Diagram

```mermaid
graph TB
    subgraph "Internet & DNS Layer"
        USER[👤 Users/Clients]
        R53[🌐 Route53 DNS<br/>Latency-Based Routing]
    end
    
    subgraph "AWS Region (e.g., eu-west-1)"
        subgraph "VPC: 172.31.0.0/16"
            subgraph "Internet Gateway Layer"
                IGW[🌐 Internet Gateway<br/>aws_internet_gateway]
                RT[📋 Route Table<br/>aws_route_table<br/>0.0.0.0/0 → IGW]
            end
            
            subgraph "Public Subnet Layer"
                SUBNET_A[📍 Public Subnet A<br/>172.31.0.0/20<br/>eu-west-1a]
                SUBNET_B[📍 Public Subnet B<br/>172.31.16.0/20<br/>eu-west-1b]
                SUBNET_C[📍 Public Subnet C<br/>172.31.32.0/20<br/>eu-west-1c]
            end
            
            subgraph "Load Balancer Layer"
                ALB[⚖️ Application Load Balancer<br/>aws_lb<br/>internet-facing<br/>Ports: 80, 443]
                
                subgraph "ALB Components"
                    LISTENER[👂 ALB Listener<br/>aws_lb_listener<br/>Port 80 → Target Group]
                    TG[🎯 Target Group<br/>aws_lb_target_group<br/>Protocol: HTTP<br/>Port: 8000<br/>Health: /health]
                end
            end
            
            subgraph "Security Layer"
                ALB_SG[🔒 ALB Security Group<br/>aws_security_group<br/>Inbound: 80,443 ← 0.0.0.0/0<br/>Outbound: 8000 → ECS SG]
                ECS_SG[🔒 ECS Security Group<br/>aws_security_group<br/>Inbound: 8001 ← ALB SG<br/>Outbound: All → 0.0.0.0/0]
            end
            
            subgraph "Container Platform Layer"
                CLUSTER[🐳 ECS Cluster<br/>aws_ecs_cluster<br/>Name: app-cluster<br/>Type: Fargate]
                
                SERVICE[⚙️ ECS Service<br/>aws_ecs_service<br/>Desired Count: 2<br/>Launch Type: FARGATE<br/>Network: awsvpc]
                
                TASK_DEF[📋 Task Definition<br/>aws_ecs_task_definition<br/>CPU: 1024 1 vCPU<br/>Memory: 3072 MB<br/>Network: awsvpc]
                
                subgraph "Running Tasks"
                    TASK1[📦 ECS Task 1<br/>Container: app-server<br/>Port: 8001<br/>Status: RUNNING]
                    TASK2[📦 ECS Task 2<br/>Container: app-server<br/>Port: 8001<br/>Status: RUNNING]
                end
            end
            
            subgraph "Service Discovery Layer" 
                SD_NS[🗺️ Service Discovery Namespace<br/>aws_service_discovery_private_dns_namespace<br/>app-services]
                SD_SVC[📋 Service Discovery Service<br/>aws_service_discovery_service<br/>DNS: app.app-services<br/>TTL: 60s]
            end
            
            subgraph "Monitoring & Logging Layer"
                CW_LOG[📊 CloudWatch Log Group<br/>aws_cloudwatch_log_group<br/>/ecs/app-task<br/>Retention: 7 days]
            end
        end
    end
    
    subgraph "Shared AWS Services"
        SECRETS[🔐 Secrets Manager<br/>API_KEY<br/>Region: Primary]
        IAM_EXEC[👤 ECS Execution Role<br/>ECR, CloudWatch, Secrets]
        IAM_TASK[👤 ECS Task Role<br/>Application permissions]
    end
    
    %% Connections
    USER --> R53
    R53 --> ALB
    IGW --> ALB
    ALB --> LISTENER
    LISTENER --> TG
    TG --> TASK1
    TG --> TASK2
    
    %% Network Flow
    SUBNET_A -.-> RT
    SUBNET_B -.-> RT
    SUBNET_C -.-> RT
    RT --> IGW
    
    %% Security
    ALB -.-> ALB_SG
    TASK1 -.-> ECS_SG
    TASK2 -.-> ECS_SG
    ALB_SG --> ECS_SG
    
    %% Container Platform
    CLUSTER --> SERVICE
    SERVICE --> TASK_DEF
    SERVICE --> TASK1
    SERVICE --> TASK2
    
    %% Service Discovery
    SERVICE --> SD_SVC
    SD_SVC --> SD_NS
    TASK1 -.-> SD_SVC
    TASK2 -.-> SD_SVC
    
    %% Monitoring
    TASK1 --> CW_LOG
    TASK2 --> CW_LOG
    
    %% IAM & Secrets
    TASK_DEF --> IAM_EXEC
    TASK_DEF --> IAM_TASK
    TASK1 --> SECRETS
    TASK2 --> SECRETS
    

    
    class CLUSTER,SERVICE,TASK_DEF,TASK1,TASK2 compute
    class IGW,RT,SUBNET_A,SUBNET_B,SUBNET_C,ALB,LISTENER,TG network
    class ALB_SG,ECS_SG,IAM_EXEC,IAM_TASK security
    class CW_LOG,SECRETS,SD_NS,SD_SVC storage
    class USER,R53 external
```

## 🚀 Quick Start Guide

### Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Terraform >= 1.0** installed
3. **API Key** for your application
4. **Route53 Hosted Zone** (optional, for custom domain)

### Single Region Deployment

```bash
# 1. Clone and navigate to terraform directory
cd terraform/fmp-mcp-modular

# 2. Copy and configure variables
cp terraform.tfvars.example terraform-my-region.tfvars
# Edit terraform-my-region.tfvars with your values

# 3. Initialize terraform
terraform init

# 4. Plan deployment
terraform plan -var-file="terraform-my-region.tfvars" -out="my-region.tfplan"

# 5. Apply deployment
terraform apply my-region.tfplan

# 6. Get deployment outputs
terraform output
```

### Multi-Region Deployment

For multiple regions, repeat the process with region-specific configuration files:

```bash
# Region 1: EU West 1
terraform plan -var-file="terraform-eu-west-1.tfvars" -state="terraform-eu-west-1.tfstate" -out="eu-west-1.tfplan"
terraform apply -state="terraform-eu-west-1.tfstate" -state-out="terraform-eu-west-1.tfstate" eu-west-1.tfplan

# Region 2: EU West 2  
terraform plan -var-file="terraform-eu-west-2.tfvars" -state="terraform-eu-west-2.tfstate" -out="eu-west-2.tfplan"
terraform apply -state="terraform-eu-west-2.tfstate" -state-out="terraform-eu-west-2.tfstate" eu-west-2.tfplan
```

### Setting up API Keys

After deployment, set your API key in AWS Secrets Manager:

```bash
# Get the secret ARN from terraform output
SECRET_ARN=$(terraform output -raw secret_arn)

# Update the secret value
aws secretsmanager put-secret-value \
  --secret-id $SECRET_ARN \
  --secret-string '{"API_KEY":"your-actual-api-key-here"}'

# Restart ECS tasks to pick up new secret
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --force-new-deployment
```

## 📊 Configuration Variables

### Core Settings
```hcl
project_name = "my-app"
environment  = "dev"
aws_region   = "eu-west-1"
```

### Network Configuration
```hcl
vpc_cidr             = "172.31.0.0/16"
availability_zones   = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
subnet_cidrs        = ["172.31.0.0/20", "172.31.16.0/20", "172.31.32.0/20"]
```

### Container Configuration
```hcl
container_image = "ghcr.io/your-org/your-app:latest"
container_port  = 8001
cpu             = 1024  # 1 vCPU
memory          = 3072  # 3 GB
desired_count   = 2     # Number of tasks
```

### Domain Configuration (Optional)
```hcl
enable_domain = true
domain_name   = "your-domain.com"
subdomain     = "api"    # Creates api.your-domain.com
```

### Weekend Scheduling (Cost Optimization)
```hcl
enable_weekend_only               = false  # Set to true for weekend-only operation
destroy_albs_when_scaled_down    = false  # Set to true for maximum cost savings
weekend_hours_start              = 6      # 6 AM UTC
weekend_hours_end                = 22     # 10 PM UTC
```

## 🔧 Management Operations

### Health Monitoring

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --services $(terraform output -raw ecs_service_name)

# View application logs
aws logs tail $(terraform output -raw cloudwatch_log_group_name) --follow

# Check load balancer target health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-load-balancers \
    --names $(terraform output -raw ecs_cluster_name | sed 's/cluster/alb/') \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text | \
    xargs aws elbv2 describe-target-groups --load-balancer-arn | \
    jq -r '.TargetGroups[0].TargetGroupArn')
```

### Application Access

```bash
# Get application URL
echo "Application URL: $(terraform output -raw application_url)"

# Test health endpoint
curl $(terraform output -raw application_url)/health

# Test API endpoint (adjust path as needed)
curl $(terraform output -raw application_url)/api/
```

### Scaling Operations

```bash
# Scale task count
terraform apply -var-file="terraform-my-region.tfvars" -var="desired_count=4"

# Scale CPU/Memory
terraform apply -var-file="terraform-my-region.tfvars" -var="cpu=2048" -var="memory=4096"

# Emergency scale down
terraform apply -var-file="terraform-my-region.tfvars" -var="desired_count=0"
```

### Cost Management

```bash
# Enable weekend-only mode
terraform apply -var-file="terraform-my-region.tfvars" \
  -var="enable_weekend_only=true" \
  -var="destroy_albs_when_scaled_down=false"

# Manual weekend scaling
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --desired-count 2

# Manual scale down
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --desired-count 0
```

## 🌐 Multi-Region Setup with Route53

For global deployment with latency-based routing:

```bash
# 1. Deploy to multiple regions
terraform apply -var-file="terraform-eu-west-1.tfvars" \
  -state="terraform-eu-west-1.tfstate" \
  -state-out="terraform-eu-west-1.tfstate"

terraform apply -var-file="terraform-eu-west-2.tfvars" \
  -state="terraform-eu-west-2.tfstate" \
  -state-out="terraform-eu-west-2.tfstate"

# 2. Check Route53 records are created
aws route53 list-resource-record-sets \
  --hosted-zone-id $(aws route53 list-hosted-zones \
    --query 'HostedZones[?Name==`your-domain.com.`].Id' \
    --output text | cut -d/ -f3)

# 3. Test latency-based routing
curl -H "Host: api.your-domain.com" http://api.your-domain.com/health
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Tasks not starting** | ECS shows pending tasks | Check IAM roles, security groups, secrets |
| **Health checks failing** | ALB shows unhealthy targets | Verify `/health` endpoint returns HTTP 200 |
| **Cannot access application** | Connection timeouts | Check security group rules, VPC routing |
| **Secrets not accessible** | Container startup errors | Verify IAM permissions for Secrets Manager |

### Debug Commands

```bash
# ECS service events
aws ecs describe-services \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --services $(terraform output -raw ecs_service_name) \
  --query 'services[0].events'

# View task logs
aws logs get-log-events \
  --log-group-name $(terraform output -raw cloudwatch_log_group_name) \
  --log-stream-name "ecs/$(terraform output -raw ecs_service_name)/$(aws ecs list-tasks \
    --cluster $(terraform output -raw ecs_cluster_name) \
    --service $(terraform output -raw ecs_service_name) \
    --query 'taskArns[0]' --output text | cut -d/ -f3)"

# Security group audit
aws ec2 describe-security-groups \
  --group-ids $(terraform output -raw ecs_security_group_id)
```

## 💰 Cost Analysis

### Typical Monthly Costs (2 tasks, 1 vCPU, 3GB memory)

| Component | 24/7 Cost | Weekend-Only Cost |
|-----------|-----------|-------------------|
| **Fargate Tasks** | $78.57 | $11.12 |
| **Application Load Balancer** | $16.43 | $16.43 (kept) or $2.33 (weekend) |
| **Other Services** | $2.50 | $2.50 |
| **Total per Region** | $97.50 | $30.05 (keep ALB) / $16.95 (weekend ALB) |

**Savings: 69-83% with weekend-only mode**

## 🌐 Multi-Region Architecture

```mermaid
graph TB
    subgraph "Internet"
        User[👤 Users]
        Domain[🌐 app.your-domain.com]
    end
    
    subgraph "Route 53 DNS"
        R53[📍 Latency-Based Routing]
        R53 --> R53_EU1[eu-west-1 Record]
        R53 --> R53_EU2[eu-west-2 Record] 
        R53 --> R53_US1[us-east-1 Record]
    end
    
    subgraph "EU-West-1 Region" 
        ALB1[⚖️ Application Load Balancer]
        ECS1[🐳 ECS Fargate Cluster]
        VPC1[🔒 VPC 172.31.0.0/16]
        ALB1 --> ECS1
    end
    
    subgraph "EU-West-2 Region"
        ALB2[⚖️ Application Load Balancer]
        ECS2[🐳 ECS Fargate Cluster]
        VPC2[🔒 VPC 172.32.0.0/16]
        ALB2 --> ECS2
    end
    
    subgraph "US-East-1 Region"
        ALB3[⚖️ Application Load Balancer]
        ECS3[🐳 ECS Fargate Cluster]
        VPC3[🔒 VPC 172.33.0.0/16]
        ALB3 --> ECS3
    end
    
    subgraph "Shared Services"
        SM[🔐 Secrets Manager]
        CW[📊 CloudWatch Logs]
        CM[🗺️ Cloud Map Service Discovery]
    end
    
    User --> Domain
    Domain --> R53
    R53_EU1 --> ALB1
    R53_EU2 --> ALB2
    R53_US1 --> ALB3
    
    ECS1 --> SM
    ECS2 --> SM
    ECS3 --> SM
    
    ECS1 --> CW
    ECS2 --> CW
    ECS3 --> CW
    
    ECS1 --> CM
    ECS2 --> CM
    ECS3 --> CM
```

## 🗂️ File Structure

```
terraform/fmp-mcp-modular/
├── main.tf                      # Provider configuration
├── variables.tf                 # Variable declarations
├── outputs.tf                   # Output definitions
├── ecs.tf                       # ECS cluster, service, tasks
├── network.tf                   # VPC, subnets, security groups
├── load_balancer.tf             # ALB, target groups, listeners
├── iam.tf                       # IAM roles and policies
├── secrets.tf                   # Secrets Manager integration
├── service_discovery.tf         # AWS Cloud Map configuration
├── route53.tf                   # Route53 DNS integration
├── weekend-schedule.tf          # Weekend-only scheduling logic
├── terraform.tfvars.example     # Sample configuration template
├── terraform-eu-west-1.tfvars   # EU West 1 configuration
├── terraform-eu-west-2.tfvars   # EU West 2 configuration
└── README.md                    # This file
```

## 🔒 Security Best Practices

### Network Security
- **Dedicated VPCs** with custom CIDR ranges per region
- **Security Groups** with least-privilege access (ALB → ECS only)
- **Public subnets** for ALB only, ECS tasks use public IPs for internet access
- **No direct SSH access** to containers (use ECS Exec if needed)

### IAM Security
- **Separate roles** for ECS execution vs. application runtime
- **Minimal permissions** following AWS best practices
- **Service-linked roles** for AWS service integrations
- **No hardcoded credentials** in code or configuration

### Secrets Management
- **AWS Secrets Manager** for API keys and sensitive data
- **Automatic rotation** capabilities (can be enabled)
- **Encryption at rest and in transit**
- **Fine-grained IAM access** to secrets

## 🔄 Cleanup

### Single Region Cleanup

```bash
# Scale down to zero first (optional, for faster cleanup)
terraform apply -var-file="terraform-my-region.tfvars" -var="desired_count=0"

# Destroy all resources
terraform destroy -var-file="terraform-my-region.tfvars"
```

### Multi-Region Cleanup

```bash
# Destroy each region separately
terraform destroy -var-file="terraform-eu-west-1.tfvars" \
  -state="terraform-eu-west-1.tfstate"

terraform destroy -var-file="terraform-eu-west-2.tfvars" \
  -state="terraform-eu-west-2.tfstate"

# Clean up Route53 records if needed
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch file://delete-records.json
```

### Clean State Files

```bash
# Remove all terraform state and cache files
rm -rf .terraform/
rm -f .terraform.lock.hcl
rm -f terraform*.tfstate*
rm -f terraform*.tfplan
```

This infrastructure provides a robust, cost-effective, and scalable foundation for containerized applications with enterprise-grade features and intelligent cost management.