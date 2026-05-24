# Maintainer Action Checklist

Items only the project maintainer (Scott Houghton, NebusAI) can do. These unblock the rest of the H1–H10 sequence in [SUBMISSION-PLAN.md](./SUBMISSION-PLAN.md).

## Hackathon (H1)

- [ ] Access the official rules page at `devpost.team/google-cloud-for-startups/hackathons/3197` and confirm:
  - Exact deadline (current assumption: ~June 5, 2026)
  - Track name and eligibility for an existing-project update
  - Required Google products checklist (Vertex AI Agent Builder, ADK, Agent Runtime, Memory Bank, Gemini)
  - Maximum team size (we are single-person)
  - Public-repo eligibility (Apache-2.0 + does not contain other parties' closed IP)
  - Submission form URL on DevPost

## GCP project (`olympuscloud-dev`)

- [ ] Enable APIs:

  ```bash
  gcloud services enable aiplatform.googleapis.com --project olympuscloud-dev
  gcloud services enable discoveryengine.googleapis.com --project olympuscloud-dev
  ```

- [ ] Create the agent service account and grant Vertex AI roles:

  ```bash
  gcloud iam service-accounts create pantheon-agent-engine-dev \
    --project olympuscloud-dev \
    --display-name "Pantheon Agent Engine (dev)"

  gcloud projects add-iam-policy-binding olympuscloud-dev \
    --member "serviceAccount:pantheon-agent-engine-dev@olympuscloud-dev.iam.gserviceaccount.com" \
    --role roles/aiplatform.user

  gcloud projects add-iam-policy-binding olympuscloud-dev \
    --member "serviceAccount:pantheon-agent-engine-dev@olympuscloud-dev.iam.gserviceaccount.com" \
    --role roles/aiplatform.reasoningEngineServiceAgent
  ```

- [ ] Confirm GCS Startup Credit covers Vertex AI Agent Engine / Reasoning Engine usage for the duration of the hackathon (Vertex Agent Runtime billing model + Memory Bank storage). If not covered, set a hard budget cap so we cannot accidentally overspend.

## Repo allowlist

- [ ] Add `OlympusCloud/olympus-hackathon-2026` to this environment's authorized-repos allowlist (same constraint that blocked `olympus-cloud-doc` from sandbox automation). Once added, the H9 sandbox e2e gate (`make demo` from a clean machine in the sandbox) becomes runnable.

## Submission (H10)

- [ ] DevPost account confirmation (Scott already has one) and submission form pre-filled with:
  - Project name + tagline
  - Demo video URL (unlisted YouTube or similar)
  - Repo URL: <https://github.com/OlympusCloud/olympus-hackathon-2026>
  - Architecture diagram URL
  - Survey answers (finalized per H10 ac-2)

## Why these are blockers (not nice-to-haves)

- Without Vertex APIs enabled in `olympuscloud-dev`, H4 (Terraform) and H5 (deploy) cannot run.
- Without the service account, the agent has no identity for Memory Bank reads/writes.
- Without GCS credit confirmation, we risk a surprise bill from Vertex Agent Runtime sustained-traffic pricing.
- Without the rules page, we are guessing at the deadline (the planning doc lists `~June 5, 2026` as an inferred target).

Once these are cleared, the remaining H2–H8 work is self-contained and can be executed without further maintainer-only steps.
