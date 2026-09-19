import hashlib

def stream_hash(filepath: str, chunk_size: int = 8 * 1024 * 1024) -> str:
    """
    Calculates SHA-256 hash of a file using memory-efficient chunking.
    Never loads the entire file into RAM.
    """
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        # If available in Python 3.11+, use file_digest for optimal performance
        if hasattr(hashlib, 'file_digest'):
            return hashlib.file_digest(f, 'sha256').hexdigest()
        
        # Fallback for older Python versions
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()
