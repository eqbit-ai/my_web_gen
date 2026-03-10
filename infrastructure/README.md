# Meydan Free Zone - AWS Infrastructure

## Architecture Overview

```
                    ┌─────────────────────────────────────────────────┐
                    │                  CloudFront CDN                  │
                    └──────────┬──────────────────┬───────────────────┘
                               │                  │
                         /api/*│            Static Assets
                               │                  │
                    ┌──────────▼──────┐  ┌────────▼──────────┐
                    │   ALB (HTTPS)   │  │    S3 Bucket      │
                    │  idle=300s SSE  │  │  uploads + sites  │
                    └──────┬──────────┘  └───────────────────┘
                           │
              ┌────────────┼────────────┐
              │                         │
    ┌─────────▼─────────┐   ┌──────────▼──────────┐
    │   ECS Fargate     │   │   ECS Fargate       │
    │   API Service     │   │   Worker Service    │
    │   (2-10 tasks)    │   │   (2-20 tasks)      │
    │   1024 CPU/2GB    │   │   512 CPU/1GB       │
    └────────┬──────────┘   └──────────┬──────────┘
             │                         │
        ┌────┴────────┬────────────────┘
        │             │
┌───────▼──────┐  ┌───▼──────────┐
│  RDS Postgres │  │ ElastiCache  │
│  15 Multi-AZ  │  │ Redis 7.0    │
│  db.t3.medium │  │ cache.t3.sm  │
└──────────────┘  └──────────────┘
```

**Region:** me-south-1 (Bahrain) - closest AWS region to UAE/Dubai.

## Directory Structure

```
infrastructure/aws/
├── cloudformation.yml      # Full stack CloudFormation template
├── ecs-task-api.json       # API task definition (standalone)
├── ecs-task-worker.json    # Worker task definition (standalone)
├── ecs-service-api.json    # API service config + auto-scaling
├── ecs-service-worker.json # Worker service config + auto-scaling
├── alb.json                # ALB config template
├── deploy.sh               # Manual deployment script
└── github-deploy.yml       # GitHub Actions CI/CD workflow
```

## Quick Start

### 1. Deploy the CloudFormation Stack

```bash
aws cloudformation create-stack \
  --stack-name meydan-staging \
  --template-body file://infrastructure/aws/cloudformation.yml \
  --parameters \
    ParameterKey=Environment,ParameterValue=staging \
    ParameterKey=DBMasterPassword,ParameterValue=YOUR_SECURE_PASSWORD \
    ParameterKey=DomainName,ParameterValue=meydan.ae \
  --capabilities CAPABILITY_NAMED_IAM \
  --region me-south-1
```

### 2. Set API Keys in Secrets Manager

After the stack is created, update the placeholder secrets:

```bash
# OpenAI API key
aws secretsmanager put-secret-value \
  --secret-id meydan/staging/openai-api-key \
  --secret-string "sk-your-openai-key" \
  --region me-south-1

# Anthropic API key
aws secretsmanager put-secret-value \
  --secret-id meydan/staging/anthropic-api-key \
  --secret-string "sk-ant-your-anthropic-key" \
  --region me-south-1
```

### 3. Build and Deploy

```bash
# Using the deploy script
chmod +x infrastructure/aws/deploy.sh
./infrastructure/aws/deploy.sh staging

# Or using GitHub Actions (push to main triggers staging deploy)
git push origin main
```

## Required AWS Secrets (GitHub Actions)

Set these in your GitHub repository settings under Settings > Secrets and variables > Actions:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key with ECS/ECR permissions |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `ECR_REGISTRY` | ECR registry URL (e.g., `123456789.dkr.ecr.me-south-1.amazonaws.com`) |

## Resources Created by CloudFormation

| Resource | Type | Details |
|----------|------|---------|
| VPC | Networking | 10.0.0.0/16 with 2 public + 2 private subnets |
| NAT Gateway | Networking | Allows private subnets to call LLM APIs |
| ECS Cluster | Compute | Fargate with Container Insights |
| API Service | Compute | 2-10 tasks, 1 vCPU / 2 GB each |
| Worker Service | Compute | 2-20 tasks, 0.5 vCPU / 1 GB each |
| RDS PostgreSQL 15 | Database | Multi-AZ, encrypted, 50-200 GB gp3 |
| ElastiCache Redis 7 | Cache | Job queue and session cache |
| ALB | Load Balancer | HTTPS with 300s idle timeout for SSE |
| S3 Bucket | Storage | Uploads and generated website assets |
| CloudFront | CDN | Static assets + API proxy |
| ECR | Registry | API and Frontend image repositories |
| ACM Certificate | Security | Wildcard SSL for domain |
| Secrets Manager | Security | DB URL, Redis URL, JWT, API keys |
| CloudWatch Logs | Monitoring | 30-day retention for API and Worker |
| Route 53 | DNS | Hosted zone placeholder |

## Auto-Scaling Policies

### API Service
- **Min:** 2 tasks, **Max:** 10 tasks
- Scale out when CPU > 60%
- Scale out when memory > 70%
- Scale-in cooldown: 5 minutes
- Scale-out cooldown: 1 minute

### Worker Service
- **Min:** 2 tasks, **Max:** 20 tasks
- Scale out when CPU > 70%
- Custom metric: Redis queue depth (target: 5 jobs per worker)
- Requires a Lambda or CloudWatch agent to push `RedisQueueDepth` metric

## Estimated Monthly Costs (Staging)

| Resource | Specification | Estimated Cost |
|----------|--------------|----------------|
| ECS Fargate (API, 2 tasks) | 1 vCPU, 2 GB | ~$60 |
| ECS Fargate (Workers, 4 tasks) | 0.5 vCPU, 1 GB | ~$60 |
| RDS PostgreSQL | db.t3.medium, Multi-AZ | ~$130 |
| ElastiCache Redis | cache.t3.small | ~$25 |
| ALB | Standard | ~$25 |
| NAT Gateway | Per GB + hourly | ~$35 |
| S3 + CloudFront | Moderate usage | ~$10 |
| CloudWatch Logs | 30-day retention | ~$5 |
| Secrets Manager | 5 secrets | ~$2 |
| **Total (staging)** | | **~$350/month** |

Production costs will be higher due to more tasks and scaling events. Budget ~$500-800/month for production with moderate traffic.

## Key Design Decisions

1. **Bahrain region (me-south-1):** Lowest latency to UAE/Dubai users.
2. **300s ALB idle timeout:** Website generation via SSE can take 30-60 seconds; 300s provides ample buffer.
3. **Sticky sessions:** SSE connections must stay on the same task for the duration of generation.
4. **NAT Gateway:** Workers need outbound internet to call OpenAI and Anthropic APIs.
5. **Multi-AZ RDS:** Production-grade reliability for tenant data.
6. **Private subnets for compute:** ECS tasks and databases are not publicly accessible.
7. **Rolling deployments:** min 50% healthy ensures zero-downtime deploys.
8. **ECR lifecycle policy:** Keeps last 10 images to control storage costs.

## Troubleshooting

### View service logs
```bash
aws logs tail /ecs/meydan-api --follow --region me-south-1
aws logs tail /ecs/meydan-worker --follow --region me-south-1
```

### Check service status
```bash
aws ecs describe-services \
  --cluster meydan-staging \
  --services meydan-api-staging meydan-worker-staging \
  --region me-south-1 \
  --query 'services[].{Name:serviceName,Status:status,Running:runningCount,Desired:desiredCount}'
```

### Force redeploy (no code changes)
```bash
aws ecs update-service --cluster meydan-staging --service meydan-api-staging --force-new-deployment --region me-south-1
```

### Connect to RDS (via bastion or SSM)
```bash
aws ssm start-session --target <bastion-instance-id> --region me-south-1
# Then from bastion:
psql -h <rds-endpoint> -U meydan -d meydan_db
```
