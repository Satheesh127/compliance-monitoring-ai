"""
Utility Functions
================

This module provides helper functions for logging, file operations,
and other common tasks used throughout the knowledge assistant.

Functions:
- setup_logging(): Sets up logging configuration
- log_step(message): Logs a processing step
- validate_url(url): Validates if a URL is properly formatted
- format_time_elapsed(start_time): Formats elapsed time
"""

import os
import re
import time
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional

from backend.core.config import FALLBACK_MESSAGE, MIN_STATEMENT_SUPPORT_RATIO

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up logging configuration for the application.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file (Optional[str]): Path to log file (None for console only)
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if needed
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    configured_logger = logging.getLogger("KnowledgeAssistant")
    configured_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    configured_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    for handler in handlers:
        handler.setFormatter(formatter)
        configured_logger.addHandler(handler)

    return configured_logger


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", (text or "").lower())}


def _split_statements(answer: str) -> List[str]:
    """Split model output into simple factual statements for validation."""
    parts = re.split(r"\n+|(?<=[.!?])\s+", (answer or "").strip())
    return [p.strip(" -\t") for p in parts if p and len(_tokenize(p)) >= 4]


def _statement_supported(statement: str, context_sentences: List[str]) -> bool:
    """Check whether a statement is directly supported by at least one context sentence."""
    st_tokens = _tokenize(statement)
    if not st_tokens:
        return False

    has_negation = any(tok in {"not", "never", "no", "without"} for tok in statement.lower().split())
    best_overlap = 0.0
    negation_aligned = not has_negation

    for sent in context_sentences:
        sent_tokens = _tokenize(sent)
        if not sent_tokens:
            continue
        overlap = len(st_tokens.intersection(sent_tokens)) / len(st_tokens)
        if overlap > best_overlap:
            best_overlap = overlap

        if has_negation and overlap >= MIN_STATEMENT_SUPPORT_RATIO:
            sent_has_negation = any(tok in {"not", "never", "no", "without"} for tok in sent.lower().split())
            negation_aligned = sent_has_negation

    return best_overlap >= MIN_STATEMENT_SUPPORT_RATIO and negation_aligned


def _validate_answer_against_context(answer: str, context_text: str) -> tuple[str, bool]:
    """Remove unsupported statements; return fallback if no grounded content remains."""
    statements = _split_statements(answer)
    if not statements:
        return FALLBACK_MESSAGE, False

    context_sentences = [s.strip() for s in re.split(r"\n+|(?<=[.!?])\s+", context_text) if s.strip()]
    supported = [s for s in statements if _statement_supported(s, context_sentences)]

    if not supported:
        return FALLBACK_MESSAGE, False

    return "\n".join(f"- {s}" for s in supported), len(supported) == len(statements)


def _query_overlap(question: str, text: str) -> float:
    question_tokens = _tokenize(question)
    doc_tokens = _tokenize(text)
    return (len(question_tokens.intersection(doc_tokens)) / len(question_tokens)) if question_tokens else 0.0


def log_step(message: str, step_num: Optional[int] = None) -> None:
    """
    Logs a processing step with consistent formatting.
    
    Args:
        message (str): Step description
        step_num (Optional[int]): Step number
    """
    if step_num:
        logger.info(f"Step {step_num}: {message}")
    else:
        logger.info(message)


def validate_url(url: str) -> bool:
    """
    Validates if a URL is properly formatted.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme) and parsed.scheme in ['http', 'https']
    except Exception:
        return False


def safe_filename(text: str, max_length: int = 50) -> str:
    """
    Creates a safe filename from text by removing invalid characters.
    
    Args:
        text (str): Text to convert to filename
        max_length (int): Maximum filename length
        
    Returns:
        str: Safe filename
    """
    # Remove or replace invalid characters
    safe_text = re.sub(r'[<>:"/\\|?*]', '_', text)
    
    # Replace spaces with underscores
    safe_text = safe_text.replace(' ', '_')
    
    # Remove multiple underscores
    safe_text = re.sub(r'_+', '_', safe_text)
    
    # Trim to max length
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length]
    
    # Remove leading/trailing underscores
    safe_text = safe_text.strip('_')
    
    return safe_text or 'unnamed'


def format_time_elapsed(start_time: float) -> str:
    """
    Formats elapsed time in a human-readable format.
    
    Args:
        start_time (float): Start time (from time.time())
        
    Returns:
        str: Formatted elapsed time
    """
    elapsed = time.time() - start_time
    
    if elapsed < 60:
        return f"{elapsed:.1f} seconds"
    elif elapsed < 3600:
        minutes = int(elapsed / 60)
        seconds = elapsed % 60
        return f"{minutes}m {seconds:.1f}s"
    else:
        hours = int(elapsed / 3600)
        minutes = int((elapsed % 3600) / 60)
        return f"{hours}h {minutes}m"


def ensure_directory_exists(directory: str) -> bool:
    """
    Ensures a directory exists, creating it if necessary.
    
    Args:
        directory (str): Directory path
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory '{directory}': {str(e)}")
        return False


def count_words(text: str) -> int:
    """
    Counts words in text.
    
    Args:
        text (str): Text to count words in
        
    Returns:
        int: Number of words
    """
    if not text:
        return 0
    
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncates text to a maximum length.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add when truncating
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def save_json_safely(data, filepath: str, indent: int = 2) -> bool:
    """
    Saves data to JSON file with error handling.
    
    Args:
        data: Data to save (must be JSON serializable)
        filepath (str): Path to save file
        indent (int): JSON indentation
        
    Returns:
        bool: True if successful, False otherwise
    """
    import json
    
    try:
        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            ensure_directory_exists(directory)
        
        # Save data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving JSON to '{filepath}': {str(e)}")
        return False


def load_json_safely(filepath: str):
    """
    Loads data from JSON file with error handling.
    
    Args:
        filepath (str): Path to JSON file
        
    Returns:
        Data from JSON file, or None if error
    """
    import json
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from '{filepath}': {str(e)}")
        return None


def print_progress_bar(current: int, total: int, prefix: str = "", bar_length: int = 30) -> None:
    """
    Prints a progress bar to console.
    
    Args:
        current (int): Current progress
        total (int): Total items
        prefix (str): Prefix text
        bar_length (int): Length of progress bar
    """
    if total == 0:
        return
    
    progress = current / total
    filled_length = int(bar_length * progress)
    
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    percent = progress * 100
    
    print(f'\r{prefix} |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
    
    if current == total:
        print()  # New line when complete


def get_file_size_mb(filepath: str) -> float:
    """
    Gets file size in megabytes.
    
    Args:
        filepath (str): Path to file
        
    Returns:
        float: File size in MB, or 0 if file doesn't exist
    """
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)  # Convert to MB
    except Exception:
        return 0.0


def create_timestamp() -> str:
    """
    Creates a timestamp string for filenames or logging.
    
    Returns:
        str: Timestamp in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def summarize_file_stats(directory: str) -> dict:
    """
    Summarizes statistics about files in a directory.
    
    Args:
        directory (str): Directory to analyze
        
    Returns:
        dict: Statistics about the directory
    """
    if not os.path.exists(directory):
        return {"error": f"Directory '{directory}' not found"}
    
    stats = {
        "total_files": 0,
        "total_size_mb": 0.0,
        "file_types": {},
        "largest_file": {"name": "", "size_mb": 0.0},
        "directory": directory
    }
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath):
            stats["total_files"] += 1
            
            # File size
            size_mb = get_file_size_mb(filepath)
            stats["total_size_mb"] += size_mb
            
            # Track largest file
            if size_mb > stats["largest_file"]["size_mb"]:
                stats["largest_file"] = {"name": filename, "size_mb": size_mb}
            
            # File type
            ext = os.path.splitext(filename)[1].lower()
            stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
    
    # Round total size
    stats["total_size_mb"] = round(stats["total_size_mb"], 2)
    stats["largest_file"]["size_mb"] = round(stats["largest_file"]["size_mb"], 2)
    
    return stats
