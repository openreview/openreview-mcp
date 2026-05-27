#!/bin/bash
# Deploy openreview-mcp to Cloud Run.
# Run from the repo root after any code change.
#
# Usage: ./deploy.sh

set -euo pipefail

PROJECT_ID="sunlit-realm-131518"
REGION="us-central1"
SERVICE="openreview-mcp"
IMAGE="us-docker.pkg.dev/${PROJECT_ID}/openreview-images/${SERVICE}"

echo "Building image (linux/amd64, CLONE_OPENREVIEW_PY=true)..."
docker build --platform linux/amd64 \
  --build-arg CLONE_OPENREVIEW_PY=true \
  -t "${IMAGE}:latest" .

echo "Pushing to Artifact Registry..."
docker push "${IMAGE}:latest"

echo "Deploying to Cloud Run..."
gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}:latest" \
  --region="${REGION}" \
  --project="${PROJECT_ID}"

echo ""
echo "Done. Service URL:"
gcloud run services describe "${SERVICE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)"