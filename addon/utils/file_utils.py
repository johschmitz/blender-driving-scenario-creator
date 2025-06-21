"""
File operation utility functions for the Driving Scenario Creator add-on.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from ..core.exceptions import FileOperationError


def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path object for the directory
        
    Raises:
        FileOperationError: If directory creation fails
    """
    try:
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        raise FileOperationError(f"Failed to create directory '{directory_path}': {str(e)}")


def safe_remove_file(file_path: Union[str, Path]) -> bool:
    """
    Safely remove a file if it exists.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file was removed or didn't exist, False if removal failed
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
        return True
    except Exception:
        return False


def safe_remove_directory(directory_path: Union[str, Path]) -> bool:
    """
    Safely remove a directory and its contents if it exists.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        True if directory was removed or didn't exist, False if removal failed
    """
    try:
        path = Path(directory_path)
        if path.exists():
            shutil.rmtree(path)
        return True
    except Exception:
        return False


def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
    """
    Copy a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if copy succeeded, False otherwise
        
    Raises:
        FileOperationError: If copy operation fails
    """
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            raise FileOperationError(f"Source file does not exist: {source}")
        
        # Ensure destination directory exists
        ensure_directory(dest_path.parent)
        
        shutil.copy2(source_path, dest_path)
        return True
    except Exception as e:
        raise FileOperationError(f"Failed to copy file from '{source}' to '{destination}': {str(e)}")


def move_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
    """
    Move a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if move succeeded, False otherwise
        
    Raises:
        FileOperationError: If move operation fails
    """
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            raise FileOperationError(f"Source file does not exist: {source}")
        
        # Ensure destination directory exists
        ensure_directory(dest_path.parent)
        
        shutil.move(str(source_path), str(dest_path))
        return True
    except Exception as e:
        raise FileOperationError(f"Failed to move file from '{source}' to '{destination}': {str(e)}")


def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Read text content from a file.
    
    Args:
        file_path: Path to the file
        encoding: Text encoding to use
        
    Returns:
        File content as string
        
    Raises:
        FileOperationError: If read operation fails
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileOperationError(f"File does not exist: {file_path}")
        
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        raise FileOperationError(f"Failed to read file '{file_path}': {str(e)}")


def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
    """
    Write text content to a file.
    
    Args:
        file_path: Path to the file
        content: Content to write
        encoding: Text encoding to use
        
    Raises:
        FileOperationError: If write operation fails
    """
    try:
        path = Path(file_path)
        
        # Ensure directory exists
        ensure_directory(path.parent)
        
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
    except Exception as e:
        raise FileOperationError(f"Failed to write file '{file_path}': {str(e)}")


def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileOperationError: If read or parse operation fails
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileOperationError(f"JSON file does not exist: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FileOperationError(f"Invalid JSON in file '{file_path}': {str(e)}")
    except Exception as e:
        raise FileOperationError(f"Failed to read JSON file '{file_path}': {str(e)}")


def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
    """
    Write JSON data to a file.
    
    Args:
        file_path: Path to the JSON file
        data: Data to write as JSON
        indent: JSON indentation level
        
    Raises:
        FileOperationError: If write operation fails
    """
    try:
        path = Path(file_path)
        
        # Ensure directory exists
        ensure_directory(path.parent)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise FileOperationError(f"Failed to write JSON file '{file_path}': {str(e)}")


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    Get the file extension from a path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension (without dot)
    """
    return Path(file_path).suffix.lstrip('.')


def change_file_extension(file_path: Union[str, Path], new_extension: str) -> Path:
    """
    Change the extension of a file path.
    
    Args:
        file_path: Original file path
        new_extension: New extension (with or without dot)
        
    Returns:
        New path with changed extension
    """
    path = Path(file_path)
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension
    return path.with_suffix(new_extension)


def get_unique_filename(file_path: Union[str, Path]) -> Path:
    """
    Get a unique filename by appending a number if the file already exists.
    
    Args:
        file_path: Desired file path
        
    Returns:
        Unique file path
    """
    path = Path(file_path)
    if not path.exists():
        return path
    
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    
    counter = 1
    while True:
        new_name = f"{stem}_{counter:03d}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def list_files_with_extension(directory: Union[str, Path], extension: str) -> List[Path]:
    """
    List all files with a specific extension in a directory.
    
    Args:
        directory: Directory to search
        extension: File extension to filter (with or without dot)
        
    Returns:
        List of file paths
        
    Raises:
        FileOperationError: If directory doesn't exist or can't be accessed
    """
    try:
        path = Path(directory)
        if not path.exists():
            raise FileOperationError(f"Directory does not exist: {directory}")
        
        if not path.is_dir():
            raise FileOperationError(f"Path is not a directory: {directory}")
        
        if not extension.startswith('.'):
            extension = '.' + extension
        
        return [f for f in path.iterdir() if f.is_file() and f.suffix.lower() == extension.lower()]
    except Exception as e:
        raise FileOperationError(f"Failed to list files in directory '{directory}': {str(e)}")


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
        
    Raises:
        FileOperationError: If file doesn't exist or can't be accessed
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileOperationError(f"File does not exist: {file_path}")
        
        return path.stat().st_size
    except Exception as e:
        raise FileOperationError(f"Failed to get file size for '{file_path}': {str(e)}")


def is_file_newer(file1: Union[str, Path], file2: Union[str, Path]) -> bool:
    """
    Check if file1 is newer than file2.
    
    Args:
        file1: First file path
        file2: Second file path
        
    Returns:
        True if file1 is newer than file2
    """
    try:
        path1 = Path(file1)
        path2 = Path(file2)
        
        if not path1.exists() or not path2.exists():
            return False
        
        return path1.stat().st_mtime > path2.stat().st_mtime
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    sanitized = ''.join('_' if c in invalid_chars else c for c in filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = 'unnamed'
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def backup_file(file_path: Union[str, Path], backup_suffix: str = '.bak') -> Optional[Path]:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        backup_suffix: Suffix for the backup file
        
    Returns:
        Path to the backup file, or None if backup failed
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        backup_path = path.with_suffix(path.suffix + backup_suffix)
        backup_path = get_unique_filename(backup_path)
        
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception:
        return None


class TemporaryDirectory:
    """
    Context manager for temporary directories.
    """
    
    def __init__(self, prefix: str = 'dsc_temp_'):
        self.prefix = prefix
        self.path: Optional[Path] = None
    
    def __enter__(self) -> Path:
        """Create temporary directory."""
        import tempfile
        self.path = Path(tempfile.mkdtemp(prefix=self.prefix))
        return self.path
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary directory."""
        if self.path and self.path.exists():
            safe_remove_directory(self.path)


# Aliases for backward compatibility
ensure_directory_exists = ensure_directory