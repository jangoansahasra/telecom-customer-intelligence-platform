"""Lightweight checks for SQL files.

These checks are intentionally simple and database-free. They catch common
project issues before we run the SQL in PostgreSQL.
"""

from __future__ import annotations

from pathlib import Path

SQL_DIRS = [Path("sql/schema"), Path("sql/models")]


def sql_files() -> list[Path]:
    files: list[Path] = []
    for directory in SQL_DIRS:
        files.extend(sorted(directory.glob("*.sql")))
    return files


def check_sql_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()

    if not stripped:
        errors.append("file is empty")

    if "telecom." not in text:
        errors.append("expected schema-qualified telecom objects")

    if path.parts[-2] == "models" and "create or replace view" not in text.lower():
        errors.append("model files should create or replace a view")

    if path.parts[-2] == "schema" and "create table" not in text.lower():
        errors.append("schema files should create tables")

    if "is_synthetic" not in text and path.parts[-2] == "schema":
        errors.append("schema files should include synthetic-data labeling")

    if not stripped.endswith(";"):
        errors.append("file should end with a semicolon")

    return errors


def main() -> None:
    files = sql_files()
    if not files:
        raise SystemExit("No SQL files found")

    all_errors: list[str] = []

    for path in files:
        errors = check_sql_file(path)
        for error in errors:
            all_errors.append(f"{path}: {error}")

    if all_errors:
        raise SystemExit("\n".join(all_errors))

    print(f"Checked {len(files)} SQL files successfully")


if __name__ == "__main__":
    main()
