from typing import Optional
from config.settings import FILE_TYPES, MAX_FILE_SIZE_MB

def validate_budget(text: str) -> Optional[int]:
    try:
        budget = int(''.join(filter(str.isdigit, text)))
        return budget if budget > 0 else None
    except (ValueError, TypeError):
        return None

def validate_file(file_name: str, file_size: int) -> bool:
    file_ext = file_name[file_name.rfind('.'):].lower()
    return (
        file_ext in FILE_TYPES and
        file_size <= MAX_FILE_SIZE_MB * 1024 * 1024
    )