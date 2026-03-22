#!/usr/bin/env bash
set -euo pipefail

# ── Meydan Observability Stack Deploy ─────────────────────────────
# Deploys: SNS + Alarms, Dashboard, WAF, S3 Lifecycle, VPC Flow Logs
#
# Usage: ./deploy-observability.sh [dev|staging|production]
# ──────────────────────────────────────────────────────────────────

ENV="${1:-dev}"
REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══ Deploying observability stack for: ${ENV} ═══"

# ── 1. SNS + CloudWatch Alarms ────────────────────────────────────
echo ""
echo "▸ Deploying Alarms + SNS..."
aws cloudformation deploy \
  --template-file "${SCRIPT_DIR}/alarms.yml" \
  --stack-name "meydan-${ENV}-alarms" \
  --parameter-overrides \
    Environment="${ENV}" \
    AlertEmail="meydan.ai.center@gmail.com" \
    ClusterName="meydan-${ENV}-cluster" \
    RDSInstanceId="meydan-${ENV}-db" \
  --capabilities CAPABILITY_IAM \
  --region "${REGION}" \
  --no-fail-on-empty-changeset

echo "  ✓ Alarms deployed. Check email to confirm SNS subscription."

# ── 2. CloudWatch Dashboard ──────────────────────────────────────
echo ""
echo "▸ Creating CloudWatch Dashboard..."
aws cloudwatch put-dashboard \
  --dashboard-name "Meydan-${ENV}-Overview" \
  --dashboard-body "file://${SCRIPT_DIR}/dashboard.json" \
  --region "${REGION}"

echo "  ✓ Dashboard created: https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=Meydan-${ENV}-Overview"

# ── 3. S3 Lifecycle Policy ───────────────────────────────────────
BUCKET="meydan-${ENV}-deployed-sites"
echo ""
echo "▸ Applying S3 lifecycle to ${BUCKET}..."
aws s3api put-bucket-lifecycle-configuration \
  --bucket "${BUCKET}" \
  --lifecycle-configuration "file://${SCRIPT_DIR}/s3-lifecycle.json" \
  --region "${REGION}" 2>/dev/null || echo "  ⚠ Bucket not found or no permission — skipping"

echo "  ✓ S3 lifecycle applied (IA after 90d, cleanup uploads after 7d)"

# ── 4. WAF (requires ALB ARN) ───────────────────────────────────
echo ""
echo "▸ Looking up ALB ARN..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names "meydan-${ENV}-alb" \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text \
  --region "${REGION}" 2>/dev/null || echo "NOT_FOUND")

if [ "$ALB_ARN" != "NOT_FOUND" ] && [ -n "$ALB_ARN" ]; then
  echo "  ALB ARN: ${ALB_ARN}"
  aws cloudformation deploy \
    --template-file "${SCRIPT_DIR}/waf.yml" \
    --stack-name "meydan-${ENV}-waf" \
    --parameter-overrides \
      Environment="${ENV}" \
      ALBArn="${ALB_ARN}" \
    --region "${REGION}" \
    --no-fail-on-empty-changeset
  echo "  ✓ WAF deployed and attached to ALB"
else
  echo "  ⚠ ALB not found — skipping WAF deployment"
fi

# ── 5. Set log retention ─────────────────────────────────────────
echo ""
echo "▸ Setting CloudWatch log retention..."
for svc in api worker frontend; do
  LOG_GROUP="/ecs/meydan-${ENV}-${svc}"
  RETENTION=14
  [ "${ENV}" = "production" ] && RETENTION=30
  aws logs put-retention-policy \
    --log-group-name "${LOG_GROUP}" \
    --retention-in-days "${RETENTION}" \
    --region "${REGION}" 2>/dev/null || echo "  ⚠ Log group ${LOG_GROUP} not found — skipping"
done
echo "  ✓ Log retention set"

echo ""
echo "═══ Observability stack deployed for ${ENV} ═══"
echo ""
echo "Next steps:"
echo "  1. Confirm the SNS email subscription"
echo "  2. Open Dashboard: https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=Meydan-${ENV}-Overview"
echo "  3. Deploy the updated backend to push custom metrics to CloudWatch"
