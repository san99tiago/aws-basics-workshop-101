#!/usr/bin/env bash
# =============================================================================
# AWS Basics Workshop 101 - deploy (or update) the private guide hosting stack
#
#   scripts/deploy.sh                       # deploy stack, guide fetched from GuideSourceUrl (GitHub)
#   scripts/deploy.sh --local               # deploy stack + upload the LOCAL guide/index.html afterwards
#   scripts/deploy.sh --delete              # delete the stack (bucket is emptied by the custom resource)
#
# Configuration via environment variables (all optional):
#   STACK_NAME          default: aws-basics-workshop-101
#   AWS_REGION          default: current CLI region or us-east-1
#   WORKSHOP_NAME       default: "AWS Basics Workshop 101"
#   INSTRUCTOR_EMAIL    default: ""
#   PARTICIPANT_EMAILS  comma separated, default: ""
#   GUIDE_PASSWORD      default: "" (no password). If set -> HTTP Basic Auth, user "workshop"
#   GUIDE_SOURCE_URL    default: raw GitHub URL of guide/index.html in this repo
#   CREATE_SES          default: true
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

STACK_NAME="${STACK_NAME:-aws-basics-workshop-101}"
AWS_REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo us-east-1)}"
WORKSHOP_NAME="${WORKSHOP_NAME:-AWS Basics Workshop 101}"
INSTRUCTOR_EMAIL="${INSTRUCTOR_EMAIL:-}"
PARTICIPANT_EMAILS="${PARTICIPANT_EMAILS:-}"
GUIDE_PASSWORD="${GUIDE_PASSWORD:-}"
GUIDE_SOURCE_URL="${GUIDE_SOURCE_URL:-https://raw.githubusercontent.com/san99tiago/aws-basics-workshop-101/main/guide/index.html}"
CREATE_SES="${CREATE_SES:-true}"
TEMPLATE="cloudformation/workshop-guide-hosting.yaml"

if [[ "${1:-}" == "--delete" ]]; then
  echo ">> Deleting stack ${STACK_NAME} in ${AWS_REGION} ..."
  aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$AWS_REGION"
  aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"
  echo ">> Deleted."
  exit 0
fi

echo ">> Validating template ..."
aws cloudformation validate-template --template-body "file://${TEMPLATE}" --region "$AWS_REGION" >/dev/null

# CommaDelimitedList parameters need commas escaped when passed through --parameter-overrides
ESCAPED_EMAILS="${PARTICIPANT_EMAILS//,/\\,}"

echo ">> Deploying stack ${STACK_NAME} in ${AWS_REGION} ..."
aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --template-file "$TEMPLATE" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset \
  --tags Project=aws-basics-workshop-101 \
  --parameter-overrides \
    "WorkshopName=${WORKSHOP_NAME}" \
    "InstructorEmail=${INSTRUCTOR_EMAIL}" \
    "ParticipantEmails=${ESCAPED_EMAILS}" \
    "GuideAccessPassword=${GUIDE_PASSWORD}" \
    "GuideSourceUrl=${GUIDE_SOURCE_URL}" \
    "CreateSesIdentities=${CREATE_SES}"

get_output() { aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
BUCKET="$(get_output GuideBucketName)"
DIST_ID="$(get_output DistributionId)"
URL="$(get_output GuideUrl)"

if [[ "${1:-}" == "--local" ]]; then
  echo ">> Uploading LOCAL guide/index.html with parameters injected ..."
  ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
  NOW="$(date -u +'%Y-%m-%d %H:%M UTC')"
  TMP="$(mktemp -t guide).html"
  sed -e "s|__WORKSHOP_NAME__|${WORKSHOP_NAME}|g" \
      -e "s|__PARTICIPANT_EMAILS__|${PARTICIPANT_EMAILS}|g" \
      -e "s|__INSTRUCTOR_EMAIL__|${INSTRUCTOR_EMAIL}|g" \
      -e "s|__AWS_REGION__|${AWS_REGION}|g" \
      -e "s|__AWS_ACCOUNT_ID__|${ACCOUNT_ID}|g" \
      -e "s|__DEPLOYED_AT__|${NOW}|g" guide/index.html > "$TMP"
  aws s3 cp "$TMP" "s3://${BUCKET}/index.html" --content-type "text/html; charset=utf-8" --cache-control "max-age=300" --region "$AWS_REGION"
  aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" >/dev/null
  rm -f "$TMP"
fi

echo
echo "=============================================================="
echo " Guide URL : ${URL}"
[[ -n "$GUIDE_PASSWORD" ]] && echo " Access    : user 'workshop' / password from GUIDE_PASSWORD"
echo " Bucket    : ${BUCKET}"
echo " CloudFront: ${DIST_ID}"
echo "=============================================================="
