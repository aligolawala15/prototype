from __future__ import annotations

from pathlib import Path
import hashlib
import random
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


INPUT = (
    ROOT
    / "data"
    / "input"
    / "archive_file_002.txt"
)

FILE_ID = "FILE_002"

FRAGMENT_SIZE = 256

GROUP_SIZE = 4

SEED = 42


# ============================================================
# DNA <-> packed 2-bit representation
# ============================================================

DNA_TO_BITS = {
    "A": 0b00,
    "C": 0b01,
    "G": 0b10,
    "T": 0b11,
}

BITS_TO_DNA = {
    0b00: "A",
    0b01: "C",
    0b10: "G",
    0b11: "T",
}


def dna_to_bytes(
    sequence: str,
) -> bytes:

    if len(sequence) % 4 != 0:

        raise ValueError(
            "DNA length must be divisible by 4."
        )

    output = bytearray()

    for index in range(
        0,
        len(sequence),
        4,
    ):

        value = 0

        for base in sequence[
            index:index + 4
        ]:

            if base not in DNA_TO_BITS:

                raise ValueError(
                    f"Invalid DNA base: {base}"
                )

            value = (
                value << 2
            ) | DNA_TO_BITS[base]

        output.append(value)

    return bytes(output)


def bytes_to_dna(
    payload: bytes,
) -> str:

    output = []

    for value in payload:

        output.append(
            BITS_TO_DNA[
                (value >> 6) & 0b11
            ]
        )

        output.append(
            BITS_TO_DNA[
                (value >> 4) & 0b11
            ]
        )

        output.append(
            BITS_TO_DNA[
                (value >> 2) & 0b11
            ]
        )

        output.append(
            BITS_TO_DNA[
                value & 0b11
            ]
        )

    return "".join(output)


# ============================================================
# XOR parity
# ============================================================

def xor_bytes(
    values: list[bytes],
) -> bytes:

    if not values:

        raise ValueError(
            "No values supplied."
        )

    length = len(values[0])

    for value in values:

        if len(value) != length:

            raise ValueError(
                "All parity inputs must have equal length."
            )

    result = bytearray(length)

    for value in values:

        for index, byte in enumerate(value):

            result[index] ^= byte

    return bytes(result)


def create_parity(
    sequences: list[str],
) -> str:

    packed = [
        dna_to_bytes(sequence)
        for sequence in sequences
    ]

    parity = xor_bytes(packed)

    return bytes_to_dna(parity)


def recover_missing_sequence(
    known_sequences: list[str],
    parity_sequence: str,
) -> str:

    values = [
        dna_to_bytes(sequence)
        for sequence in known_sequences
    ]

    values.append(
        dna_to_bytes(parity_sequence)
    )

    recovered = xor_bytes(values)

    return bytes_to_dna(recovered)


# ============================================================
# Integrity helper
# ============================================================

def sha256(
    value: str,
) -> str:

    return hashlib.sha256(
        value.encode("ascii")
    ).hexdigest()


def corrupt_one_base(
    sequence: str,
    seed: int,
) -> str:

    rng = random.Random(seed)

    bases = list(sequence)

    index = rng.randrange(
        len(bases)
    )

    original = bases[index]

    alternatives = [
        base
        for base in "ACGT"
        if base != original
    ]

    bases[index] = rng.choice(
        alternatives
    )

    return "".join(bases)


# ============================================================
# Fragment metadata
# ============================================================

def fragment_address(
    fragment,
) -> str:

    return (
        f"{fragment.file_id}"
        f"-FRAG-"
        f"{fragment.fragment_id:06d}"
    )


# ============================================================
# Build parity groups
# ============================================================

def build_groups(
    fragments,
):

    groups = []

    for start in range(
        0,
        len(fragments),
        GROUP_SIZE,
    ):

        group = fragments[
            start:start + GROUP_SIZE
        ]

        if len(group) != GROUP_SIZE:

            raise ValueError(
                "Dataset must contain complete parity groups."
            )

        groups.append(group)

    return groups


# ============================================================
# Main
# ============================================================

def main():

    print("")
    print("=" * 60)
    print("MILESTONE 8 VERIFICATION")
    print("REDUNDANCY + SINGLE-FRAGMENT RECOVERY")
    print("=" * 60)
    print("")

    # --------------------------------------------------------
    # Load original file
    # --------------------------------------------------------

    original = INPUT.read_bytes()

    original_hash = hashlib.sha256(
        original
    ).hexdigest()

    # --------------------------------------------------------
    # Encode to DNA
    # --------------------------------------------------------

    fragments = encode_file_to_dna_fragments(
        INPUT,
        file_id=FILE_ID,
        fragment_size=FRAGMENT_SIZE,
    )

    print("SOURCE")
    print("-" * 60)

    print(
        f"Original bytes      : "
        f"{len(original)}"
    )

    print(
        f"DNA fragments       : "
        f"{len(fragments)}"
    )

    print(
        f"Fragment size       : "
        f"{FRAGMENT_SIZE} bytes"
    )

    print(
        f"Parity group size   : "
        f"{GROUP_SIZE} data fragments"
    )

    # --------------------------------------------------------
    # Baseline reconstruction
    # --------------------------------------------------------

    baseline = decode_dna_fragments(
        fragments
    )

    baseline_success = (
        baseline == original
    )

    print("")
    print("BASELINE")
    print("-" * 60)

    print(
        f"Clean reconstruction: "
        f"{baseline_success}"
    )

    if not baseline_success:

        raise SystemExit(
            "FAIL: Clean baseline reconstruction failed."
        )

    # --------------------------------------------------------
    # Build parity
    # --------------------------------------------------------

    groups = build_groups(
        fragments
    )

    parity_records = []

    for group_index, group in enumerate(
        groups
    ):

        sequences = [
            fragment.dna_sequence
            for fragment in group
        ]

        parity_sequence = create_parity(
            sequences
        )

        parity_records.append(
            {
                "group_index": group_index,
                "parity_sequence": parity_sequence,
                "parity_hash": sha256(
                    parity_sequence
                ),
            }
        )

    print("")
    print("REDUNDANCY LAYER")
    print("-" * 60)

    print(
        f"Data fragments     : "
        f"{len(fragments)}"
    )

    print(
        f"Parity fragments   : "
        f"{len(parity_records)}"
    )

    print(
        f"Total archive units: "
        f"{len(fragments) + len(parity_records)}"
    )

    print(
        f"Redundancy overhead: "
        f"{len(parity_records) / len(fragments) * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Test 1: Missing fragment
    # --------------------------------------------------------

    target_group_index = 5

    target_group = groups[
        target_group_index
    ]

    target_position = 2

    missing_target = target_group[
        target_position
    ]

    known_sequences = [
        fragment.dna_sequence
        for index, fragment in enumerate(
            target_group
        )
        if index != target_position
    ]

    recovered_sequence = recover_missing_sequence(
        known_sequences,
        parity_records[
            target_group_index
        ]["parity_sequence"],
    )

    recovery_matches = (
        recovered_sequence
        == missing_target.dna_sequence
    )

    print("")
    print("MISSING-FRAGMENT RECOVERY")
    print("-" * 60)

    print(
        f"Target group       : "
        f"{target_group_index}"
    )

    print(
        f"Missing address    : "
        f"{fragment_address(missing_target)}"
    )

    print(
        f"Known fragments    : "
        f"{len(known_sequences)}"
    )

    print(
        f"Parity available   : "
        f"True"
    )

    print(
        f"Sequence recovered : "
        f"{recovery_matches}"
    )

    if not recovery_matches:

        raise SystemExit(
            "FAIL: Missing fragment recovery failed."
        )

    # --------------------------------------------------------
    # Reconstruct complete file after recovery
    # --------------------------------------------------------

    recovered_fragments = []

    for fragment in fragments:

        if (
            fragment.file_id
            == missing_target.file_id
            and
            fragment.fragment_id
            == missing_target.fragment_id
        ):

            # Replace missing DNA with recovered sequence.
            recovered_fragments.append(
                type(fragment)(
                    file_id=fragment.file_id,
                    fragment_id=fragment.fragment_id,
                    dna_sequence=recovered_sequence,
                )
            )

        else:

            recovered_fragments.append(
                fragment
            )

    recovered_fragments.sort(
        key=lambda fragment:
        fragment.fragment_id
    )

    reconstructed = decode_dna_fragments(
        recovered_fragments
    )

    reconstructed_hash = hashlib.sha256(
        reconstructed
    ).hexdigest()

    missing_reconstruction = (
        reconstructed
        == original
    )

    print("")
    print("MISSING-FRAGMENT FILE RECOVERY")
    print("-" * 60)

    print(
        f"Original bytes       : "
        f"{len(original)}"
    )

    print(
        f"Recovered bytes      : "
        f"{len(reconstructed)}"
    )

    print(
        f"Exact reconstruction : "
        f"{missing_reconstruction}"
    )

    print(
        f"Original SHA-256     : "
        f"{original_hash}"
    )

    print(
        f"Recovered SHA-256    : "
        f"{reconstructed_hash}"
    )

    if not missing_reconstruction:

        raise SystemExit(
            "FAIL: Complete file recovery failed."
        )

    # --------------------------------------------------------
    # Test 2: One corrupted fragment
    # --------------------------------------------------------

    corruption_group_index = 7

    corruption_group = groups[
        corruption_group_index
    ]

    corruption_position = 1

    corrupted_target = corruption_group[
        corruption_position
    ]

    corrupted_sequence = corrupt_one_base(
        corrupted_target.dna_sequence,
        seed=12345,
    )

    corrupted_known_sequences = [
        corrupted_sequence
        if index == corruption_position
        else fragment.dna_sequence
        for index, fragment in enumerate(
            corruption_group
        )
        if index != corruption_position
    ]

    recovered_from_corruption = (
        recover_missing_sequence(
            corrupted_known_sequences,
            parity_records[
                corruption_group_index
            ]["parity_sequence"],
        )
    )

    corruption_recovery_matches = (
        recovered_from_corruption
        == corrupted_target.dna_sequence
    )

    print("")
    print("CORRUPTED-FRAGMENT RECOVERY")
    print("-" * 60)

    print(
        f"Target address     : "
        f"{fragment_address(corrupted_target)}"
    )

    print(
        f"Original hash      : "
        f"{sha256(corrupted_target.dna_sequence)[:20]}..."
    )

    print(
        f"Corrupted hash     : "
        f"{sha256(corrupted_sequence)[:20]}..."
    )

    print(
        f"Corruption detected: "
        f"{corrupted_sequence != corrupted_target.dna_sequence}"
    )

    print(
        f"Recovered original : "
        f"{corruption_recovery_matches}"
    )

    if not corruption_recovery_matches:

        raise SystemExit(
            "FAIL: Corrupted fragment recovery failed."
        )

    # --------------------------------------------------------
    # Reconstruct file after corruption recovery
    # --------------------------------------------------------

    corruption_recovered_fragments = []

    for fragment in fragments:

        if (
            fragment.file_id
            == corrupted_target.file_id
            and
            fragment.fragment_id
            == corrupted_target.fragment_id
        ):

            corruption_recovered_fragments.append(
                type(fragment)(
                    file_id=fragment.file_id,
                    fragment_id=fragment.fragment_id,
                    dna_sequence=recovered_from_corruption,
                )
            )

        else:

            corruption_recovered_fragments.append(
                fragment
            )

    corruption_recovered_fragments.sort(
        key=lambda fragment:
        fragment.fragment_id
    )

    corruption_reconstructed = (
        decode_dna_fragments(
            corruption_recovered_fragments
        )
    )

    corruption_recovery_success = (
        corruption_reconstructed
        == original
    )

    corruption_hash = hashlib.sha256(
        corruption_reconstructed
    ).hexdigest()

    print("")
    print("CORRUPTED-FRAGMENT FILE RECOVERY")
    print("-" * 60)

    print(
        f"Original bytes       : "
        f"{len(original)}"
    )

    print(
        f"Recovered bytes      : "
        f"{len(corruption_reconstructed)}"
    )

    print(
        f"Exact reconstruction : "
        f"{corruption_recovery_success}"
    )

    print(
        f"Original SHA-256     : "
        f"{original_hash}"
    )

    print(
        f"Recovered SHA-256    : "
        f"{corruption_hash}"
    )

    if not corruption_recovery_success:

        raise SystemExit(
            "FAIL: Corrupted-file recovery failed."
        )

    # --------------------------------------------------------
    # Important limitation
    # --------------------------------------------------------

    print("")
    print("SCOPE OF THIS EXPERIMENT")
    print("-" * 60)

    print(
        "Recovery is demonstrated for ONE missing or corrupted"
    )

    print(
        "fragment within a parity group of four data fragments."
    )

    print(
        "Multiple simultaneous losses in the same group are"
    )

    print(
        "outside the recovery capability of this parity scheme."
    )

    print(
        "This experiment does not claim physical DNA reliability."
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    overall = (
        baseline_success
        and missing_reconstruction
        and corruption_recovery_success
    )

    print("")
    print("=" * 60)

    if overall:

        print("RESULT: PASS")
        print(
            "Redundancy recovered one missing DNA fragment."
        )
        print(
            "Redundancy recovered one corrupted DNA fragment."
        )
        print(
            "The original digital file was reconstructed exactly."
        )

    else:

        print("RESULT: FAIL")

    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
