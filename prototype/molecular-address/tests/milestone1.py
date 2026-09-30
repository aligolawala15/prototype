from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.encoding.dna import (
    bytes_to_bits,
    bits_to_bytes,
    bytes_to_dna,
    dna_to_bytes,
)


INPUT = ROOT / "data" / "input" / "milestone1_sample.txt"
OUTPUT = ROOT / "data" / "generated" / "milestone1_reconstructed.txt"


def main() -> None:
    original = INPUT.read_bytes()

    # Stage 1: bytes -> bits
    bits = bytes_to_bits(original)

    # Stage 2: bits -> DNA
    dna = bytes_to_dna(original)

    # Stage 3: DNA -> bytes
    reconstructed = dna_to_bytes(dna)

    # Independent binary round-trip verification
    binary_roundtrip = bits_to_bytes(bits)

    OUTPUT.write_bytes(reconstructed)

    print("")
    print("=" * 60)
    print("MILESTONE 1 VERIFICATION")
    print("=" * 60)
    print(f"Input file       : {INPUT}")
    print(f"Output file      : {OUTPUT}")
    print(f"Original bytes   : {len(original)}")
    print(f"Binary length    : {len(bits)} bits")
    print(f"DNA length       : {len(dna)} bases")
    print(f"Binary roundtrip : {binary_roundtrip == original}")
    print(f"DNA roundtrip    : {reconstructed == original}")
    print(f"Files identical  : {OUTPUT.read_bytes() == INPUT.read_bytes()}")
    print("")

    if binary_roundtrip != original:
        raise SystemExit("FAIL: Binary round-trip failed.")

    if reconstructed != original:
        raise SystemExit("FAIL: DNA round-trip failed.")

    print("RESULT: PASS")
    print("DNA encoding/decoding preserves the original bytes exactly.")
    print("=" * 60)


if __name__ == "__main__":
    main()
