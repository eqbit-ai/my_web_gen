#!/bin/bash
# =============================================================================
# Meydan Free Zone - AWS ECS Deployment Script
# =============================================================================
# Usage: ./deploy.sh [staging|production]
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Docker running locally
#   - ECR repositories created (via CloudFormation stack)
#
# Environment variables (optional overrides):
#   AWS_REGION      - AWS region (default: me-south-1 / Bahrain)
#   AWS_ACCOUNT_ID  - AWS account ID (auto-detected if not set)
#   SKIP_BUILD      - Set to "true" to skip Docker build and only deploy
# =============================================================================

set -euo pipefail

# --- Configuration ---
ENVIRONMENT=${1:-staging}
AWS_REGION=${AWS_REGION:-me-south-1}

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
  echo "Error: Environment must be 'staging' or 'production'"
  echo "Usage: ./deploy.sh [staging|production]"
  exit 1
fi

# Auto-detect AWS Account ID if not set
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Resolve paths relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "============================================="
echo "  Meydan Deployment"
echo "============================================="
echo "  Environment:  ${ENVIRONMENT}"
echo "  Region:       ${AWS_REGION}"
echo "  Account:      ${AWS_ACCOUNT_ID}"
echo "  ECR Registry: ${ECR_REGISTRY}"
echo "  Project Root: ${PROJECT_ROOT}"
echo "============================================="
echo ""

# --- Confirm production deployments ---
if [[ "$ENVIRONMENT" == "production" ]]; then
  read -p "You are about to deploy to PRODUCTION. Continue? (yes/no): " confirm
  if [[ "$confirm" != "yes" ]]; then
    echo "Deployment cancelled."
    exit 0
  fi
fi

# --- Login to ECR ---
echo "[1/5] Logging in to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ECR_REGISTRY}"
echo ""

if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
  # --- Build and push API image ---
  echo "[2/5] Building API image..."
  docker build \
    -t meydan-api:latest \
    -t "${ECR_REGISTRY}/meydan-api:${ENVIRONMENT}" \
    -t "${ECR_REGISTRY}/meydan-api:${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)" \
    "${PROJECT_ROOT}/backend"

  echo "      Pushing API image..."
  docker push "${ECR_REGISTRY}/meydan-api:${ENVIRONMENT}"
  echo ""

  # --- Build and push Frontend image ---
  echo "[3/5] Building Frontend image..."
  docker build \
    -t meydan-frontend:latest \
    -t "${ECR_REGISTRY}/meydan-frontend:${ENVIRONMENT}" \
    -t "${ECR_REGISTRY}/meydan-frontend:${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)" \
    "${PROJECT_ROOT}/frontend"

  echo "      Pushing Frontend image..."
  docker push "${ECR_REGISTRY}/meydan-frontend:${ENVIRONMENT}"
  echo ""
else
  echo "[2/5] Skipping API build (SKIP_BUILD=true)"
  echo "[3/5] Skipping Frontend build (SKIP_BUILD=true)"
  echo ""
fi

# --- Update ECS services (triggers rolling deployment) ---
echo "[4/5] Deploying API service..."
aws ecs update-service \
  --cluster "meydan-${ENVIRONMENT}" \
  --service "meydan-api-${ENVIRONMENT}" \
  --force-new-deployment \
  --region "${AWS_REGION}" \
  --query 'service.deployments[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
  --output table

echo ""
echo "[5/5] Deploying Worker service..."
aws ecs update-service \
  --cluster "meydan-${ENVIRONMENT}" \
  --service "meydan-worker-${ENVIRONMENT}" \
  --force-new-deployment \
  --region "${AWS_REGION}" \
  --query 'service.deployments[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
  --output table

echo ""
echo "============================================="
echo "  Deployment initiated successfully!"
echo "============================================="
echo ""
echo "  Monitor deployment:"
echo "  https://${AWS_REGION}.console.aws.amazon.com/ecs/v2/clusters/meydan-${ENVIRONMENT}/services?region=${AWS_REGION}"
echo ""
echo "  Wait for stable:"
echo "  aws ecs wait services-stable --cluster meydan-${ENVIRONMENT} --services meydan-api-${ENVIRONMENT} meydan-worker-${ENVIRONMENT} --region ${AWS_REGION}"
echo ""
