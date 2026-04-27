# 7. Deployment Runbook

Two flavours: **routine deploy** (push to a branch — CI does the rest) and **first-time provisioning** (clean cloud account → running production).

## Routine deploy — push and CI does it

| Branch | CI workflow | AWS account | Region |
|---|---|---|---|
| `dev` | `.github/workflows/deploy-dev.yml` | `371170753756` | `us-east-1` |
| `main` | `.github/workflows/deploy-prod.yml` | `290172088819` | `ap-southeast-1` (Singapore) |

Each workflow:
1. Builds `meydan-api` and `meydan-frontend` images with `--platform linux/amd64`.
2. Pushes to ECR.
3. `aws ecs update-service --force-new-deployment` on each of the 3 services (api, worker, frontend).
4. `aws ecs wait services-stable` (up to ~10 min).

`entrypoint.sh` runs `alembic upgrade head` before gunicorn boots — migrations apply automatically.

> **Known annoyance**: the wait step occasionally times out on a successful deploy. If `/api/health` returns 200 within 5 min of the push, treat the deploy as green.

## Prerequisites

### Accounts
- AWS account with administrator access. Production region: **`ap-southeast-1`** (Singapore). Dev region: **`us-east-1`**.
- GitHub access to the private `meydan-website-generator` repo.
- AWS Route 53 hosted zone for `meydanfzai.com` (apex + wildcard records).
- OpenProvider reseller account.
- Resend account, `meydanfzai.com` domain verified (SPF + DKIM TXT records).
- OpenAI + Anthropic API keys (production tier — see `10_known_issues_and_support.md` for tier requirements at scale).

### Local tools
- Docker Desktop (for `--platform linux/amd64` cross-build — **required**, not optional).
- AWS CLI v2.
- GitHub CLI (optional).
- Node 20+, Python 3.12, `psql` 15 client.

### Secrets
All listed in `08_environment_and_secrets.md`.

## First-time provisioning — clean account → running prod

> Throughout, set `export AWS_REGION=ap-southeast-1 && export AWS_PROFILE=prod`.

### 1. ECR + Secrets Manager (free / near-free)
```bash
aws ecr create-repository --repository-name meydan-api --image-scanning-configuration scanOnPush=true
aws ecr create-repository --repository-name meydan-frontend --image-scanning-configuration scanOnPush=true

# Populate Secrets Manager — see 08_environment_and_secrets.md for the full list.
# For each secret, IMPORTANT: strip trailing whitespace before storing or the value
# becomes an Illegal HTTP header value when injected as env var into ECS.
for s in jwt-secret openai-api-key anthropic-api-key resend-api-key openprovider-username \
         openprovider-password openprovider-reseller-id pexels-api-key unsplash-access-key \
         gemini-api-key; do
  read -p "Value for meydan/prod/$s: " v
  printf '%s' "$v" > /tmp/sec.txt   # printf, not echo — no trailing newline
  aws secretsmanager create-secret --name "meydan/prod/$s" --secret-string "file:///tmp/sec.txt"
done
shred -u /tmp/sec.txt
```

### 2. Network (VPC + subnets + IGW + SGs)
```bash
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.10.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=meydan-prod-vpc}]' \
  --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support

# Public subnets in 3 AZs
for i in a b c; do
  aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.10.$([ $i = a ] && echo 1 || ([ $i = b ] && echo 2 || echo 3)).0/24 \
    --availability-zone ap-southeast-1$i \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=meydan-prod-subnet-1$i}]"
done

# IGW, route table, security groups — see infrastructure/aws/cloudformation.yml for the parameterised version.
```

### 3. RDS (PostgreSQL 15 Multi-AZ)
```bash
DB_PASS=$(openssl rand -base64 32 | tr -d '+/=' | head -c 24)
aws rds create-db-instance \
  --db-instance-identifier meydan-prod-db \
  --db-instance-class db.t4g.medium \
  --engine postgres --engine-version 15.17 \
  --master-username meydan --master-user-password "$DB_PASS" \
  --allocated-storage 20 --max-allocated-storage 100 \
  --storage-type gp3 --storage-encrypted \
  --multi-az \
  --vpc-security-group-ids "$DB_SG" \
  --db-subnet-group-name meydan-prod-db-subnet \
  --backup-retention-period 14 \
  --deletion-protection \
  --db-name meydan_db
# Wait ~12 min until status=available, then write the URL into Secrets Manager.
```

### 4. ElastiCache Redis
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id meydan-prod-redis \
  --engine redis --cache-node-type cache.t3.small --num-cache-nodes 1 \
  --cache-subnet-group-name meydan-prod-redis-subnet \
  --security-group-ids "$REDIS_SG" \
  --snapshot-retention-limit 7
```

### 5. ALB + target groups + ACM cert
```bash
ALB_ARN=$(aws elbv2 create-load-balancer --name meydan-prod-alb --type application \
  --subnets $SUBNET_1A $SUBNET_1B $SUBNET_1C --security-groups $ALB_SG \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)
aws elbv2 modify-load-balancer-attributes --load-balancer-arn $ALB_ARN \
  --attributes Key=idle_timeout.timeout_seconds,Value=300

# Target groups: api on 8000, frontend on 3000. API uses lb_cookie stickiness for SSE.
# HTTPS listener on 443 with ACM cert; HTTP 80 redirects 301 to HTTPS.
# /api/* rule → API target group at priority 10; default → frontend.

# ACM cert with DNS validation:
aws acm request-certificate --domain-name meydanfzai.com \
  --subject-alternative-names "*.meydanfzai.com" --validation-method DNS
# Add the validation CNAME to Route 53 (or whichever DNS authority holds the zone).
```

### 6. ECS cluster + task definitions + services
```bash
aws ecs create-cluster --cluster-name meydan-prod-cluster \
  --capacity-providers FARGATE --settings name=containerInsights,value=enabled

aws ecs register-task-definition --cli-input-json file://infrastructure/aws/ecs-task-api-prod.json
aws ecs register-task-definition --cli-input-json file://infrastructure/aws/ecs-task-worker-prod.json
# Frontend task def is similar but image=meydan-frontend, port=3000, no secrets.

# Services — public subnets with assignPublicIp=ENABLED (no NAT Gateway, mirrors dev pattern).
aws ecs create-service --cluster meydan-prod-cluster \
  --service-name meydan-prod-api --task-definition meydan-prod-api \
  --desired-count 0 --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[...],securityGroups=[...],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$API_TG,containerName=meydan-api,containerPort=8000" \
  --health-check-grace-period-seconds 120

# Repeat for worker (no LB) and frontend.
```

### 7. Autoscaling
```bash
# API: 2 → 6 on CPU 60%; Worker: 1 → 8 on CPU 50%; Frontend: 2 → 4 on CPU 60%.
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/meydan-prod-cluster/meydan-prod-api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 --max-capacity 6
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs --resource-id service/meydan-prod-cluster/meydan-prod-api \
  --scalable-dimension ecs:service:DesiredCount --policy-name api-cpu-target \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{"TargetValue":60.0,"PredefinedMetricSpecification":{"PredefinedMetricType":"ECSServiceAverageCPUUtilization"},"ScaleInCooldown":300,"ScaleOutCooldown":60}'
```

### 8. Data migration (only if migrating from an existing dev environment)

See `infrastructure/migration/` helper scripts:
- `pg_dump_us_east.sh` — dump dev DB
- `pg_restore_singapore.sh` — restore (drops and recreates `public` schema first to avoid the `schema "public" already exists` error from a fresh restore)
- `s3_sync_uploads.sh` — sync customer-uploaded assets cross-region
- `verify_migration.sh` — diff row counts between dev and prod

### 9. DNS cutover (CloudFront)

```
apex (meydanfzai.com)  A   →  CNAME  →  meydan-prod-alb-XXXX.ap-southeast-1.elb.amazonaws.com  (proxied / orange-cloud)
www                    A   →  CNAME  →  same
dev                    CNAME unchanged (still points to us-east-1 ALB for testing)
```

CloudFront's CNAME-flattening handles the apex CNAME natively. Set `proxied=true` to also get DDoS + WAF + edge caching.

### 10. WAF + CloudWatch + alarms

Apply `infrastructure/aws/waf.yml`, `infrastructure/aws/alarms.yml`, `infrastructure/aws/dashboard.json` via CloudFormation / AWS CLI.

## Post-deployment checks

- `curl https://meydanfzai.com/api/health` returns `{"status":"ok","service":"meydan-website-generator"}`.
- `curl https://meydanfzai.com/` returns 200 with `Content-Type: text/html` and the React shell HTML.
- Sign up a throwaway user, generate one site, deploy it. The deployed site loads from `https://<slug>.s3-website.ap-southeast-1.amazonaws.com`.
- CloudWatch dashboard `meydan-production` panels green for 30 minutes.

## Rollback

For a bad code deploy:
```bash
# Find the previous task def revision
aws ecs describe-services --cluster meydan-prod-cluster --services meydan-prod-api \
  --query 'services[0].deployments[].{rev:taskDefinition,status:status}'

# Roll the API back
aws ecs update-service --cluster meydan-prod-cluster --service meydan-prod-api \
  --task-definition meydan-prod-api:N-1 --force-new-deployment
```

For a bad data state — restore from the latest RDS snapshot (snapshot-restore creates a new instance; you then point Secrets Manager `database-url` at the new endpoint and force-redeploy).

## Local setup — under 30 minutes for a new developer

```bash
git clone <repo>
cd meydan-website-generator

# 1. Backend
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY at minimum
docker run -d --name meydan-pg -p 5432:5432 -e POSTGRES_USER=meydan -e POSTGRES_PASSWORD=meydan -e POSTGRES_DB=meydan_db postgres:15
docker run -d --name meydan-redis -p 6379:6379 redis:7
alembic upgrade head
uvicorn app.main:app --reload --port 8000   # API on http://localhost:8000

# 2. Worker (separate terminal)
cd backend && source venv/bin/activate
python -m app.worker

# 3. Frontend (separate terminal)
cd ../frontend
npm install
npm start   # http://localhost:3000

# Or skip the manual setup and run everything via docker-compose:
docker compose up
```
