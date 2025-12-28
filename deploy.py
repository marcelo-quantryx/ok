#!/usr/bin/env python3
"""Create a Prefect Managed deployment for the OK Mobility scraper.

This mirrors the example you provided for the Instagram project.

Usage:
  source .venv/bin/activate
  python deploy_prefect_managed.py

Notes:
- The repository must be pushed to GitHub so Prefect Managed can fetch it.
- You must be logged into Prefect Cloud via the CLI for this script to succeed.
"""

from datetime import timedelta
from pathlib import Path
from prefect.runner.storage import GitRepository

from prefect_flow import main_flow


# Official Prefect images for Prefect Managed workers
PREFECT_IMAGE = "prefecthq/prefect:3-python3.12"

# Update this to your GitHub repository URL (must be accessible by Prefect Cloud)
GITHUB_REPO = "https://github.com/marcelo-quantryx/ok"


def _read_requirements(path: str = "requirements.txt"):
    p = Path(path)
    if not p.exists():
        return []
    lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines()]
    pkgs = [l for l in lines if l and not l.startswith("#")]
    return pkgs


def main():
    print("Deploying OK Mobility scraper to Prefect Managed (work pool: default)")
    print(f"Source: {GITHUB_REPO}")
    print(f"Image: {PREFECT_IMAGE}")

    pip_packages = _read_requirements()

    # Deploy the flow, instructing workers to install pip packages at runtime
    main_flow.from_source(
        source=GitRepository(url=GITHUB_REPO),
        entrypoint="prefect_flow.py:main_flow",
    ).deploy(
        name="okmobility-every-5m",
        work_pool_name="default",
        interval=timedelta(minutes=5),
        description="Scrape OK Mobility availability every 5 minutes",
        tags=["okmobility", "scraper"],
        image=PREFECT_IMAGE,
        job_variables={
            "pip_packages": pip_packages,
        },
    )

    print("Deployment created (or updated) in Prefect Cloud.")


if __name__ == "__main__":
    main()
