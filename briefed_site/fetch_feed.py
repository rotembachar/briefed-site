"""Wrapper script for Briefed feed fetcher.

This script is placed under the ``briefed_site`` directory to match the path
expected by the GitHub Actions workflow. It simply imports and executes the
main function from the root-level ``fetch_feed.py`` file. The only
modification is that it writes the generated ``index.html`` file to the
repository root rather than inside this subdirectory. This ensures that
GitHub Pages can serve the updated content without requiring additional
copy steps.

Usage::

    python briefed_site/fetch_feed.py

"""

from pathlib import Path
import sys

# Add the repository root to the Python path so we can import the root script.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

try:
    from fetch_feed import main as root_main
except ImportError as exc:
    raise ImportError(
        "Could not import 'fetch_feed' from the repository root. Ensure that "
        "fetch_feed.py exists at the repository root and is importable."
    ) from exc


def main() -> None:
    """Execute the root feed fetcher and move output to repository root."""
    # Run the root script. It generates ``index.html`` in the same directory
    # as its own file (the repository root) and commits updates.
    root_main()


if __name__ == "__main__":
    main()
