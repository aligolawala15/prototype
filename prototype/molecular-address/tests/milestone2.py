from __future__ import annotations

from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.fragmentation.fragmenter import (
    fragment_file,
    reconstruct_fragments,
)


INPUT = ROOT / "data" / "input" / "milestone2_10kb.txt"

FILE_ID = "FILE_001"
FRAGMENT_SIZE = 256


def check_unique_addresses(fragments):
    addresses = [fragment.address for fragment in fragments]

    return len(addresses) == len(set(addresses))


def main() -> None:
    print("")
    print("=" * 60)
    print("MILESTONE 2 VERIFICATION")
    print("=" * 60)

    original = INPUT.read_bytes()

    # --------------------------------------------------------
    # Fragment
    # --------------------------------------------------------

    fragments = fragment_file(
        input_path=INPUT,
        file_id=FILE_ID,
        fragment_size=FRAGMENT_SIZE,
    )

    print(f"Input file       : {INPUT}")
    print(f"File ID          : {FILE_ID}")
    print(f"Original bytes   : {len(original)}")
    print(f"Fragment size    : {FRAGMENT_SIZE}")
    print(f"Fragment count   : {len(fragments)}")
    print("")

    # --------------------------------------------------------
    # Display fragment identities
    # --------------------------------------------------------

    print("FRAGMENT IDENTITIES")
    print("-" * 60)

    for fragment in fragments:
        print(
            f"{fragment.address:<25}"
            f"payload={fragment.payload_size:>4} bytes"
        )

    print("")

    # --------------------------------------------------------
    # Test 1: unique addresses
    # --------------------------------------------------------

    unique_addresses = check_unique_addresses(fragments)

    print(f"Unique addresses : {unique_addresses}")

    if not unique_addresses:
        raise SystemExit(
            "FAIL: Fragment addresses are not unique."
        )

    # --------------------------------------------------------
    # Test 2: shuffle fragments
    # --------------------------------------------------------

    shuffled = fragments.copy()

    random.Random(42).shuffle(shuffled)

    print(f"Shuffled order   : {[f.fragment_id for f in shuffled]}")

    # --------------------------------------------------------
    # Test 3: reconstruct shuffled fragments
    # --------------------------------------------------------

    reconstructed = reconstruct_fragments(shuffled)

    identical = reconstructed == original

    print(f"Reconstruction   : {identical}")

    if not identical:
        raise SystemExit(
            "FAIL: Reconstruction after shuffling failed."
        )

    # --------------------------------------------------------
    # Test 4: all fragments belong to one file
    # --------------------------------------------------------

    file_ids = {fragment.file_id for fragment in fragments}

    single_file_identity = file_ids == {FILE_ID}

    print(f"File identity     : {single_file_identity}")

    if not single_file_identity:
        raise SystemExit(
            "FAIL: Fragment file identities are inconsistent."
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("RESULT: PASS")
    print("Fragmentation preserves file identity and ordering.")
    print("Fragments can be shuffled and reconstructed correctly.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()

