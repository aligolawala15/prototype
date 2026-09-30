from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT),
)


from app.dna_archive.archive import (
    encode_file_to_dna_fragments,
    decode_dna_fragments,
)

from app.integrity.archive import (
    AddressedDNAArchive,
)

from app.integrity.verification import (
    verify_fragment,
)

from app.errors.address_corruption import (
    corrupt_one_fragment,
)


INPUT = (
    ROOT
    / "data"
    / "input"
    / "archive_file_002.txt"
)

FILE_ID = "FILE_002"

FRAGMENT_SIZE = 256


def main():

    print("")
    print("=" * 60)
    print("MILESTONE 7 VERIFICATION")
    print("MOLECULAR ADDRESS + INTEGRITY VERIFICATION")
    print("=" * 60)
    print("")

    # ========================================================
    # 1. Encode source file
    # ========================================================

    original = INPUT.read_bytes()

    dna_fragments = encode_file_to_dna_fragments(
        INPUT,
        file_id=FILE_ID,
        fragment_size=FRAGMENT_SIZE,
    )

    expected_fragments = len(
        dna_fragments
    )

    print("SOURCE")
    print("-" * 60)

    print(
        f"Original bytes      : "
        f"{len(original)}"
    )

    print(
        f"DNA fragments       : "
        f"{expected_fragments}"
    )

    # ========================================================
    # 2. Build addressed archive
    # ========================================================

    archive = AddressedDNAArchive(
        seed=42
    )

    archive.add_dna_fragments(
        dna_fragments
    )

    archive.seal()

    print("")
    print("ADDRESSED ARCHIVE")
    print("-" * 60)

    print(
        f"Total fragments     : "
        f"{archive.total_fragments}"
    )

    # ========================================================
    # 3. Verify clean archive
    # ========================================================

    valid, invalid = archive.verify_file(
        FILE_ID
    )

    print("")
    print("CLEAN INTEGRITY TEST")
    print("-" * 60)

    print(
        f"Valid fragments     : "
        f"{len(valid)}"
    )

    print(
        f"Invalid fragments   : "
        f"{len(invalid)}"
    )

    clean_integrity = (
        len(valid) == expected_fragments
        and
        len(invalid) == 0
    )

    print(
        f"Integrity result    : "
        f"{clean_integrity}"
    )

    if not clean_integrity:

        raise SystemExit(
            "FAIL: Clean archive failed integrity verification."
        )

    # ========================================================
    # 4. Demonstrate molecular addresses
    # ========================================================

    print("")
    print("MOLECULAR ADDRESS SAMPLE")
    print("-" * 60)

    for fragment in sorted(
        valid,
        key=lambda item: item.fragment_id,
    )[:5]:

        print(
            f"{fragment.address}"
            f" | DNA={len(fragment.dna_sequence)} bases"
            f" | HASH={fragment.integrity_hash[:16]}..."
        )

    # ========================================================
    # 5. Corrupt exactly one fragment
    # ========================================================

    target = sorted(
        valid,
        key=lambda item: item.fragment_id,
    )[10]

    corrupted_target = corrupt_one_fragment(
        target,
        seed=123,
    )

    print("")
    print("CONTROLLED CORRUPTION")
    print("-" * 60)

    print(
        f"Target address     : "
        f"{target.address}"
    )

    print(
        f"Original verified  : "
        f"{verify_fragment(target)}"
    )

    print(
        f"After corruption   : "
        f"{verify_fragment(corrupted_target)}"
    )

    if verify_fragment(
        corrupted_target
    ):

        raise SystemExit(
            "FAIL: Integrity system failed to detect corruption."
        )

    # ========================================================
    # 6. Replace the clean fragment with corrupted fragment
    # ========================================================

    modified_fragments = []

    for fragment in archive.all_fragments():

        if (
            fragment.file_id == FILE_ID
            and
            fragment.fragment_id
            == target.fragment_id
        ):

            modified_fragments.append(
                corrupted_target
            )

        else:

            modified_fragments.append(
                fragment
            )

    modified_valid = []
    modified_invalid = []

    for fragment in modified_fragments:

        if verify_fragment(fragment):

            modified_valid.append(
                fragment
            )

        else:

            modified_invalid.append(
                fragment
            )

    print("")
    print("ARCHIVE-WIDE INTEGRITY TEST")
    print("-" * 60)

    print(
        f"Valid fragments     : "
        f"{len(modified_valid)}"
    )

    print(
        f"Invalid fragments   : "
        f"{len(modified_invalid)}"
    )

    if len(modified_invalid) != 1:

        raise SystemExit(
            "FAIL: Expected exactly one invalid fragment."
        )

    detected_address = (
        modified_invalid[0].address
    )

    print(
        f"Detected address    : "
        f"{detected_address}"
    )

    print(
        f"Correct fragment    : "
        f"{detected_address == target.address}"
    )

    if (
        detected_address
        != target.address
    ):

        raise SystemExit(
            "FAIL: Wrong fragment was flagged."
        )

    # ========================================================
    # 7. Prove that valid fragments can still be isolated
    # ========================================================

    valid_same_file = [
        fragment
        for fragment in modified_valid
        if fragment.file_id == FILE_ID
    ]

    print("")
    print("VALID-DATA ISOLATION")
    print("-" * 60)

    print(
        f"Expected fragments : "
        f"{expected_fragments}"
    )

    print(
        f"Valid fragments    : "
        f"{len(valid_same_file)}"
    )

    print(
        f"Rejected fragments : "
        f"{len(modified_invalid)}"
    )

    isolation_success = (
        len(valid_same_file)
        == expected_fragments - 1
    )

    print(
        f"Isolation result   : "
        f"{isolation_success}"
    )

    if not isolation_success:

        raise SystemExit(
            "FAIL: Valid/invalid fragment isolation failed."
        )

    # ========================================================
    # 8. Demonstrate that integrity is detection, not recovery
    # ========================================================

    print("")
    print("IMPORTANT LIMITATION TEST")
    print("-" * 60)

    print(
        "Integrity verification detects corruption."
    )

    print(
        "It does not reconstruct the missing/corrupted base."
    )

    print(
        "Recovery is intentionally NOT implemented in Milestone 7."
    )

    # ========================================================
    # 9. Final result
    # ========================================================

    print("")
    print("=" * 60)
    print("RESULT: PASS")
    print("Every clean fragment passed integrity verification.")
    print("A deliberately corrupted fragment was detected.")
    print("The exact molecular address of the corrupted fragment")
    print("was identified.")
    print("Integrity detection is separated from data recovery.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
