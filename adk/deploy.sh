#!/usr/bin/env bash
# Deploy the Ceres ADK manifest to Vertex AI Agent Runtime in the
# olympuscloud-dev project. Idempotent — re-running updates the existing
# reasoning engine instead of creating a new one.
#
# Prerequisites (see ../SCOTT-ACTION-REQUIRED.md):
#   gcloud services enable aiplatform.googleapis.com discoveryengine.googleapis.com \
#     --project olympuscloud-dev
#   gcloud iam service-accounts create pantheon-agent-engine-dev ...
#   terraform apply  (in ../terraform/)
#
# Usage:
#   ./deploy.sh                    # deploy / update the dev agent
#   DRY_RUN=1 ./deploy.sh          # show the gcloud command without running it
#   AGENT_NAME=ceres-staging ./deploy.sh   # override target instance name

set -euo pipefail

PROJECT="${PROJECT:-olympuscloud-dev}"
REGION="${REGION:-us-central1}"
AGENT_NAME="${AGENT_NAME:-ceres-dev}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-pantheon-agent-engine-dev@${PROJECT}.iam.gserviceaccount.com}"
MANIFEST="$(cd "$(dirname "$0")" && pwd)/ceres.adk.yaml"

if [[ ! -f "$MANIFEST" ]]; then
  echo "manifest not found at $MANIFEST" >&2
  exit 1
fi

CMD=(
  gcloud ai reasoning-engines deploy "$AGENT_NAME"
  --project="$PROJECT"
  --region="$REGION"
  --manifest="$MANIFEST"
  --service-account="$SERVICE_ACCOUNT"
  --update-if-exists
)

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  printf 'DRY RUN — would execute:\n  %s\n' "${CMD[*]}"
  exit 0
fi

# Pre-flight: confirm caller has the right project + the manifest parses
gcloud config set project "$PROJECT" >/dev/null
if command -v yq >/dev/null; then
  yq -e '.kind == "Agent"' "$MANIFEST" >/dev/null \
    || { echo "manifest is not a valid Agent" >&2; exit 1; }
fi

echo "Deploying $AGENT_NAME to $PROJECT/$REGION..."
"${CMD[@]}"

echo
echo "Done. Endpoint URL:"
gcloud ai reasoning-engines describe "$AGENT_NAME" \
  --project="$PROJECT" --region="$REGION" \
  --format='value(endpointUri)'
