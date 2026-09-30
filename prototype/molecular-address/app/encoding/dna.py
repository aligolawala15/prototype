from __future__ import annotations

from pathlib import Path


BITS_TO_DNA = {
    "00": "A",
    "01": "C",
    "10": "G",
    "11": "T",
}

DNA_TO_BITS = {value: key for key, value in BITS_TO_DNA.items()}


def bytes_to_bits(data: bytes) -> str:
    """Convert bytes to a binary string."""
    return "".join(f"{byte:08b}" for byte in data)


def bits_to_bytes(bits: str) -> bytes:
    """Convert a binary string back to bytes."""
    if len(bits) % 8 != 0:
        raise ValueError("Bit string length must be divisible by 8.")

    if any(bit not in "01" for bit in bits):
        raise ValueError("Bit string contains invalid characters.")

    return bytes(
        int(bits[index:index + 8], 2)
        for index in range(0, len(bits), 8)
    )


def bits_to_dna(bits: str) -> str:
    """Encode 2-bit groups as DNA bases."""
    if len(bits) % 2 != 0:
        raise ValueError("Bit string length must be divisible by 2.")

    return "".join(
        BITS_TO_DNA[bits[index:index + 2]]
        for index in range(0, len(bits), 2)
    )


def dna_to_bits(dna: str) -> str:
    """Decode DNA bases back into a binary string."""
    dna = dna.upper()

    invalid = set(dna) - set(DNA_TO_BITS)
    if invalid:
        raise ValueError(
            f"DNA sequence contains invalid bases: {sorted(invalid)}"
        )

    return "".join(DNA_TO_BITS[base] for base in dna)


def bytes_to_dna(data: bytes) -> str:
    """Convert bytes directly into simulated DNA."""
    return bits_to_dna(bytes_to_bits(data))


def dna_to_bytes(dna: str) -> bytes:
    """Convert simulated DNA back into bytes."""
    return bits_to_bytes(dna_to_bits(dna))


def encode_file(input_path: str | Path) -> str:
    """Read a file and encode its contents as simulated DNA."""
    data = Path(input_path).read_bytes()
    return bytes_to_dna(data)


def decode_to_file(dna: str, output_path: str | Path) -> None:
    """Decode simulated DNA and write the reconstructed file."""
    data = dna_to_bytes(dna)
    Path(output_path).write_bytes(data)
