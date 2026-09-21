import secrets
from typing import List, Tuple, Dict

def generate_random_bitstring(length: int) -> str:
    """Generates a random bitstring of the specified length."""
    return "".join(secrets.choice('01') for _ in range(length))

def string_to_bits(s: str) -> List[int]:
    """Converts a binary string ('10101') to a list of integers [1, 0, 1, 0, 1]."""
    return [int(char) for char in s]

def bits_to_string(bits: List[int]) -> str:
    """Converts a list of bits [1, 0, 1, 0, 1] to a binary string '10101'."""
    return "".join(str(b) for b in bits)

def hamming_distance(s1: str, s2: str) -> int:
    """Calculates the Hamming distance between two binary strings of equal length."""
    if len(s1) != len(s2):
        raise ValueError(f"Strings must be of equal length (got {len(s1)} and {len(s2)})")
    dist = 0
    for c1, c2 in zip(s1, s2):
        if c1 == '_' or c2 == '_':
            dist += 1
        elif c1 != c2:
            dist += 1
    return dist

def find_best_matches(extracted_bitstring: str, codebook: List[Dict]) -> List[Tuple[Dict, float, int]]:
    """
    Compares the extracted bitstring against a codebook (list of dictionaries with a 'bitstring' key).
    Returns a sorted list of (record, confidence_percentage, distance) tuples.
    """
    results = []
    bit_len = len(extracted_bitstring)
    if bit_len == 0:
        return []

    for record in codebook:
        ref_bits = record["bitstring"]
        # Match lengths if they differ
        if len(ref_bits) != bit_len:
            # Skip or truncate/pad if necessary. Ideally they should match.
            continue
        dist = hamming_distance(extracted_bitstring, ref_bits)
        confidence = (1.0 - (dist / bit_len)) * 100.0
        results.append((record, confidence, dist))

    # Sort by confidence descending, then by distance ascending
    results.sort(key=lambda x: (-x[1], x[2]))
    return results
