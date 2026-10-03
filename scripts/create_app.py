#!/usr/bin/env python3
"""
Nexora Backend Feature Module Scaffolder

Generates a standardized Django feature module adhering to the approved
Domain-Oriented Feature-Based Modular Monolith architecture.

Approved Feature Structure:
apps/<feature>/
├── migrations/
│   └── __init__.py
├── models/
│   └── __init__.py
├── managers/
│   └── __init__.py
├── serializers/
│   └── __init__.py
├── services/
│   └── __init__.py
├── selectors/
│   └── __init__.py
├── permissions/
│   └── __init__.py
├── validators/
│   └── __init__.py
├── views/
│   └── __init__.py
├── urls/
│   └── __init__.py
├── tests/
│   └── __init__.py
├── admin.py
├── apps.py
└── __init__.py
"""

import argparse
import keyword
import re
import sys
from pathlib import Path

# Subdirectories defining the feature's internal responsibility boundaries
RESPONSIBILITY_SUBDIRECTORIES = [
    "migrations",
    "models",
    "managers",
    "serializers",
    "services",
    "selectors",
    "permissions",
    "validators",
    "views",
    "urls",
    "tests",
]

# Reserved Python & Django names that cannot be used as feature names
RESERVED_NAMES = {
    # Python keywords and builtins
    "test",
    "tests",
    "site",
    "math",
    "os",
    "sys",
    "json",
    "io",
    "re",
    "datetime",
    "types",
    "logging",
    "collections",
    # Django framework apps & core modules
    "django",
    "admin",
    "auth",
    "contenttypes",
    "sessions",
    "messages",
    "staticfiles",
    "config",
    "apps",
    "manage",
    "settings",
    "urls",
    "wsgi",
    "asgi",
    "core",
    "shared",
}


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case string to PascalCase for Django AppConfig class name."""
    return "".join(word.capitalize() for word in snake_str.split("_"))


def validate_app_name(name: str) -> None:
    """Validate app name against Python/Django naming conventions and reserved words."""
    if not name:
        raise ValueError("Feature module name cannot be empty.")

    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        raise ValueError(
            f"Invalid feature module name '{name}'. "
            "It must start with a lowercase letter and contain only lowercase letters, digits, and underscores."
        )

    if keyword.iskeyword(name):
        raise ValueError(f"Feature module name '{name}' is a reserved Python keyword.")

    if name in RESERVED_NAMES:
        raise ValueError(
            f"Feature module name '{name}' is a reserved Python or Django module name."
        )


def locate_apps_dir() -> Path:
    """Locate the backend/apps directory relative to script or current working directory."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "backend" / "apps",
        script_dir.parent / "apps",
        script_dir / "apps",
        Path.cwd() / "backend" / "apps",
        Path.cwd() / "apps",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()

    # Fallback to default expected path relative to repository root
    fallback = (script_dir.parent / "backend" / "apps").resolve()
    return fallback


def create_feature_module(app_name: str, apps_dir: Path, dry_run: bool = False) -> Path:
    """Scaffold a new feature module with approved directory structure and base files."""
    validate_app_name(app_name)

    target_dir = apps_dir / app_name

    if target_dir.exists():
        # Check if it already has files
        existing_items = list(target_dir.iterdir())
        if existing_items:
            # If it has files or non-cache directories, fail safely
            real_files = [f for f in existing_items if f.name != "__pycache__"]
            if real_files:
                raise FileExistsError(
                    f"Target app directory already exists and is not empty: {target_dir}"
                )

    pascal_name = to_pascal_case(app_name)

    apps_py_content = (
        "from django.apps import AppConfig\n\n\n"
        f"class {pascal_name}Config(AppConfig):\n"
        '    default_auto_field = "django.db.models.BigAutoField"\n'
        f'    name = "apps.{app_name}"\n'
    )

    admin_py_content = (
        "from django.contrib import admin\n\n"
        "# Register your models here.\n"
    )

    if dry_run:
        print(f"[DRY-RUN] Target directory: {target_dir}")
        print(f"[DRY-RUN] Would create directory: {target_dir}")
        print(f"[DRY-RUN] Would create file: {target_dir / '__init__.py'}")
        print(f"[DRY-RUN] Would create file: {target_dir / 'apps.py'}")
        print(f"[DRY-RUN] Would create file: {target_dir / 'admin.py'}")
        for subdir in RESPONSIBILITY_SUBDIRECTORIES:
            print(f"[DRY-RUN] Would create directory: {target_dir / subdir}")
            print(f"[DRY-RUN] Would create file: {target_dir / subdir / '__init__.py'}")
        return target_dir

    # Create root app directory
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "__init__.py").touch(exist_ok=True)
    (target_dir / "apps.py").write_text(apps_py_content, encoding="utf-8")
    (target_dir / "admin.py").write_text(admin_py_content, encoding="utf-8")

    # Create responsibility subdirectories with __init__.py
    for subdir in RESPONSIBILITY_SUBDIRECTORIES:
        sub_path = target_dir / subdir
        sub_path.mkdir(parents=True, exist_ok=True)
        (sub_path / "__init__.py").touch(exist_ok=True)

    return target_dir


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Scaffold a new Nexora backend feature module adhering to the approved modular monolith architecture."
    )
    parser.add_argument(
        "name",
        type=str,
        help="Feature module name in snake_case (e.g. learning, question_bank, assessment).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate scaffolding without creating directories or files.",
    )
    parser.add_argument(
        "--apps-dir",
        type=Path,
        default=None,
        help="Optional custom path to the apps directory.",
    )

    args = parser.parse_args()

    app_name = args.name.strip().lower()

    apps_dir = args.apps_dir.resolve() if args.apps_dir else locate_apps_dir()
    if not apps_dir.is_dir():
        print(f"Error: Apps directory does not exist at '{apps_dir}'.", file=sys.stderr)
        return 1

    try:
        target_dir = create_feature_module(app_name, apps_dir, dry_run=args.dry_run)
        if args.dry_run:
            print(f"\n[DRY-RUN] Scaffolding plan verified for 'apps.{app_name}'.")
        else:
            print(f"Successfully scaffolded feature module 'apps.{app_name}' at:\n  {target_dir}")
            print("\nCreated structure:")
            print(f"apps/{app_name}/")
            print("├── migrations/")
            print("├── models/")
            print("├── managers/")
            print("├── serializers/")
            print("├── services/")
            print("├── selectors/")
            print("├── permissions/")
            print("├── validators/")
            print("├── views/")
            print("├── urls/")
            print("├── tests/")
            print("├── admin.py")
            print("├── apps.py")
            print("└── __init__.py")
            print(f"\nRemember to register 'apps.{app_name}' in backend/config/settings/base.py INSTALLED_APPS.")
        return 0
    except (ValueError, FileExistsError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"Unexpected error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
