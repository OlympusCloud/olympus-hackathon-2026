"""Deploy the Ceres ADK agent to Vertex AI Agent Engine.

Usage:
    python deploy.py [--project olympuscloud-dev] [--location us-central1]
                     [--staging-bucket gs://...] [--display-name ceres-dev]

If --staging-bucket is omitted, the script ensures a default bucket exists
at `gs://${PROJECT}-vertex-agent-staging`.

Idempotent: re-running updates the existing Agent Engine instance instead
of creating a duplicate (matches by --display-name).

Prereqs (one-time; see ../SCOTT-ACTION-REQUIRED.md):
- Vertex AI + Discovery Engine APIs enabled
- ADC set up with quota project (`gcloud auth application-default
  set-quota-project olympuscloud-dev`)
- ../terraform applied (provides the SA + Memory Bank data stores)

The script writes the deployed agent's resource name to stdout — copy that
into ../sdk/dart-sample/lib/demo_credentials.dart as `agentResourceName`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

import vertexai
from vertexai import agent_engines

from agent import root_agent

DEFAULT_PROJECT = "olympuscloud-dev"
DEFAULT_LOCATION = "us-central1"
DEFAULT_DISPLAY_NAME = "ceres-dev"
DEFAULT_SERVICE_ACCOUNT = (
    "pantheon-agent-engine-dev@olympuscloud-dev.iam.gserviceaccount.com"
)


def ensure_staging_bucket(project: str, bucket: str) -> None:
    """Create the staging bucket if it does not exist (idempotent)."""
    existing = subprocess.run(
        ["gcloud", "storage", "buckets", "describe", bucket, f"--project={project}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if existing.returncode == 0:
        print(f"[ok] staging bucket {bucket} exists")
        return
    print(f"[create] staging bucket {bucket}")
    subprocess.run(
        [
            "gcloud", "storage", "buckets", "create", bucket,
            f"--project={project}", "--location=US",
            "--uniform-bucket-level-access",
        ],
        check=True,
    )


def find_existing(display_name: str):
    """Return the first Agent Engine matching display_name, or None."""
    for ae in agent_engines.list():
        if ae.display_name == display_name:
            return ae
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--display-name", default=DEFAULT_DISPLAY_NAME)
    parser.add_argument("--staging-bucket", default=None)
    parser.add_argument("--service-account", default=DEFAULT_SERVICE_ACCOUNT)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the deployment plan without calling Vertex AI",
    )
    args = parser.parse_args()

    bucket = args.staging_bucket or f"gs://{args.project}-vertex-agent-staging"

    print(f"project          {args.project}")
    print(f"location         {args.location}")
    print(f"display_name     {args.display_name}")
    print(f"staging_bucket   {bucket}")
    print(f"service_account  {args.service_account}")

    if args.dry_run:
        print("\n--dry-run set, exiting before any Vertex AI calls")
        return 0

    ensure_staging_bucket(args.project, bucket)

    vertexai.init(
        project=args.project,
        location=args.location,
        staging_bucket=bucket,
    )

    app = agent_engines.AdkApp(agent=root_agent)
    requirements = [
        "google-cloud-aiplatform[agent_engines,adk]",
        "google-adk",
    ]
    # Bundle the local agent package so the runtime can `import agent`.
    # Without this the deserialized AdkApp imports fail at startup.
    extra_packages = ["./agent"]

    existing = find_existing(args.display_name)
    if existing:
        print(f"\n[update] existing engine {existing.resource_name}")
        remote = existing.update(
            agent_engine=app,
            requirements=requirements,
            extra_packages=extra_packages,
        )
    else:
        print("\n[create] new engine")
        remote = agent_engines.create(
            agent_engine=app,
            requirements=requirements,
            extra_packages=extra_packages,
            display_name=args.display_name,
            description="Ceres inventory agent — hackathon submission. Faithful port of the Pantheon LangGraph workflow.",
            service_account=args.service_account,
        )

    print()
    print("=" * 60)
    print("DEPLOYED")
    print("=" * 60)
    print(f"resource_name = {remote.resource_name}")
    print()
    print("Drop into ../sdk/dart-sample/lib/demo_credentials.dart as the")
    print("agentResourceName field.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
