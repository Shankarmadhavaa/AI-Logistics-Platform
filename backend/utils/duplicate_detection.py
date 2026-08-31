import hashlib
from pathlib import Path


def calculate_file_hash(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()


def find_duplicate(
    file_hash: str,
    upload_dir: Path,
) -> Path | None:

    for file_path in upload_dir.iterdir():

        if not file_path.is_file():
            continue

        if file_path.name == ".gitkeep":
            continue

        with open(file_path, "rb") as file:
            existing_content = file.read()

        existing_hash = calculate_file_hash(existing_content)

        if existing_hash == file_hash:
            return file_path

    return None