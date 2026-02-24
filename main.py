"""
Main entrypoint for full production pipeline.
"""

from src.orchestrator import run_pipeline


if __name__ == "__main__":
    run_pipeline()