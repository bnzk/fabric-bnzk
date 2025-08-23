# Deprecated: Packaging is now configured via pyproject.toml using setuptools.
# This file is intentionally left minimal to avoid confusion if invoked.
if __name__ == "__main__":
    raise SystemExit(
        "This project uses pyproject.toml. Use standard PEP 517 builds (e.g., 'pip install .') or editable installs ('pip install -e .')."
    )
