from __future__ import annotations

from pathlib import Path
import csv
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

SEED = 9001


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


def xor_bytes(
    values: list[bytes],
) -> bytes:

    length = len(values[0])

    result = bytearray(length)

    for value in values:

        if len(value) != length:
            raise ValueError(
                "Parity inputs have different lengths."
            )

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

    return bytes_to_dna(
        xor_bytes(packed)
    )


def recover_missing(
    known_sequences: list[str],
    parity_sequence: str,
) -> str:

    packed = [
        dna_to_bytes(sequence)
        for sequence in known_sequences
    ]

    packed.append(
        dna_to_bytes(parity_sequence)
    )

    return bytes_to_dna(
        xor_bytes(packed)
    )


def fragment_address(
    fragment,
) -> str:

    return (
        f"{fragment.file_id}"
        f"-FRAG-"
        f"{fragment.fragment_id:06d}"
    )


def hash_bytes(
    value: bytes,
) -> str:

    return hashlib.sha256(
        value
    ).hexdigest()


def hash_dna(
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


def build_parity(
    fragments,
):

    parity = {}

    for start in range(
        0,
        len(fragments),
        GROUP_SIZE,
    ):

        group_index = start // GROUP_SIZE

        group = fragments[
            start:start + GROUP_SIZE
        ]

        if len(group) != GROUP_SIZE:
            raise ValueError(
                "Incomplete parity group."
            )

        parity[group_index] = create_parity(
            [
                fragment.dna_sequence
                for fragment in group
            ]
        )

    return parity


def reconstruct_with_fragments(
    fragments,
):

    ordered = sorted(
        fragments,
        key=lambda fragment:
        fragment.fragment_id,
    )

    return decode_dna_fragments(
        ordered
    )


def make_fragment(
    template,
    sequence,
):

    return type(template)(
        file_id=template.file_id,
        fragment_id=template.fragment_id,
        dna_sequence=sequence,
    )


def baseline_missing_test(
    fragments,
    target_index,
    original,
):

    remaining = [
        fragment
        for index, fragment in enumerate(
            fragments
        )
        if index != target_index
    ]

    try:

        reconstructed = reconstruct_with_fragments(
            remaining
        )

        exact = (
            reconstructed == original
        )

        return {
            "decode_completed": True,
            "exact": exact,
            "bytes": len(reconstructed),
        }

    except Exception:

        return {
            "decode_completed": False,
            "exact": False,
            "bytes": 0,
        }


def recovery_missing_test(
    fragments,
    parity,
    target_index,
    original,
):

    target = fragments[
        target_index
    ]

    group_index = (
        target.fragment_id
        // GROUP_SIZE
    )

    group_start = (
        group_index
        * GROUP_SIZE
    )

    group = fragments[
        group_start:
        group_start + GROUP_SIZE
    ]

    known = [
        fragment.dna_sequence
        for fragment in group
        if fragment.fragment_id
        != target.fragment_id
    ]

    recovered_sequence = recover_missing(
        known,
        parity[group_index],
    )

    recovered_fragment = make_fragment(
        target,
        recovered_sequence,
    )

    rebuilt = []

    for index, fragment in enumerate(
        fragments
    ):

        if index == target_index:

            rebuilt.append(
                recovered_fragment
            )

        else:

            rebuilt.append(
                fragment
            )

    reconstructed = (
        reconstruct_with_fragments(
            rebuilt
        )
    )

    return {
        "recovered": (
            recovered_sequence
            == target.dna_sequence
        ),
        "exact": (
            reconstructed == original
        ),
        "bytes": len(reconstructed),
    }


def baseline_corruption_test(
    fragments,
    target_index,
    original,
):

    target = fragments[
        target_index
    ]

    corrupted = corrupt_one_base(
        target.dna_sequence,
        SEED + target_index,
    )

    damaged = []

    for index, fragment in enumerate(
        fragments
    ):

        if index == target_index:

            damaged.append(
                make_fragment(
                    fragment,
                    corrupted,
                )
            )

        else:

            damaged.append(
                fragment
            )

    try:

        reconstructed = (
            reconstruct_with_fragments(
                damaged
            )
        )

        exact = (
            reconstructed == original
        )

        return {
            "decode_completed": True,
            "exact": exact,
            "bytes": len(reconstructed),
        }

    except Exception:

        return {
            "decode_completed": False,
            "exact": False,
            "bytes": 0,
        }


def recovery_corruption_test(
    fragments,
    parity,
    target_index,
    original,
):

    target = fragments[
        target_index
    ]

    group_index = (
        target.fragment_id
        // GROUP_SIZE
    )

    group_start = (
        group_index
        * GROUP_SIZE
    )

    group = fragments[
        group_start:
        group_start + GROUP_SIZE
    ]

    corrupted = corrupt_one_base(
        target.dna_sequence,
        SEED + target_index,
    )

    detected = (
        corrupted
        != target.dna_sequence
    )

    known = [
        fragment.dna_sequence
        for fragment in group
        if fragment.fragment_id
        != target.fragment_id
    ]

    recovered_sequence = recover_missing(
        known,
        parity[group_index],
    )

    recovered_fragment = make_fragment(
        target,
        recovered_sequence,
    )

    rebuilt = []

    for index, fragment in enumerate(
        fragments
    ):

        if index == target_index:

            rebuilt.append(
                recovered_fragment
            )

        else:

            rebuilt.append(
                fragment
            )

    reconstructed = (
        reconstruct_with_fragments(
            rebuilt
        )
    )

    return {
        "detected": detected,
        "recovered": (
            recovered_sequence
            == target.dna_sequence
        ),
        "exact": (
            reconstructed == original
        ),
        "bytes": len(reconstructed),
    }


def main():

    print("")
    print("=" * 60)
    print("MILESTONE 9 VERIFICATION")
    print("BASELINE VS RECOVERY COMPARISON")
    print("=" * 60)
    print("")

    original = INPUT.read_bytes()

    original_hash = hash_bytes(
        original
    )

    fragments = (
        encode_file_to_dna_fragments(
            INPUT,
            file_id=FILE_ID,
            fragment_size=FRAGMENT_SIZE,
        )
    )

    parity = build_parity(
        fragments
    )

    print("DATASET")
    print("-" * 60)

    print(
        f"Original bytes       : "
        f"{len(original)}"
    )

    print(
        f"DNA fragments        : "
        f"{len(fragments)}"
    )

    print(
        f"Parity fragments     : "
        f"{len(parity)}"
    )

    print(
        f"Redundancy overhead  : "
        f"{len(parity) / len(fragments) * 100:.2f}%"
    )

    print(
        f"Original SHA-256     : "
        f"{original_hash}"
    )

    # --------------------------------------------------------
    # Baseline verification
    # --------------------------------------------------------

    clean = reconstruct_with_fragments(
        fragments
    )

    if clean != original:

        raise SystemExit(
            "FAIL: Clean baseline reconstruction failed."
        )

    print("")
    print("CLEAN BASELINE")
    print("-" * 60)

    print(
        "Clean reconstruction : True"
    )

    # --------------------------------------------------------
    # Controlled target fragments
    # --------------------------------------------------------

    missing_targets = [
        2,
        10,
        18,
        26,
        34,
    ]

    corruption_targets = [
        5,
        13,
        21,
        29,
        37,
    ]

    rows = []

    # --------------------------------------------------------
    # Missing-fragment comparison
    # --------------------------------------------------------

    print("")
    print("MISSING-FRAGMENT COMPARISON")
    print("-" * 60)

    print(
        "Target | Baseline Exact | "
        "Recovery | Recovery Exact"
    )

    for target_index in missing_targets:

        baseline = baseline_missing_test(
            fragments,
            target_index,
            original,
        )

        recovered = recovery_missing_test(
            fragments,
            parity,
            target_index,
            original,
        )

        address = fragment_address(
            fragments[target_index]
        )

        print(
            f"{address} | "
            f"{baseline['exact']} | "
            f"{recovered['recovered']} | "
            f"{recovered['exact']}"
        )

        rows.append(
            {
                "experiment": "missing",
                "address": address,
                "baseline_exact": baseline[
                    "exact"
                ],
                "recovery_success": recovered[
                    "recovered"
                ],
                "final_exact": recovered[
                    "exact"
                ],
            }
        )

    # --------------------------------------------------------
    # Corruption comparison
    # --------------------------------------------------------

    print("")
    print("CORRUPTED-FRAGMENT COMPARISON")
    print("-" * 60)

    print(
        "Target | Baseline Exact | "
        "Detected | Recovered | Recovery Exact"
    )

    for target_index in corruption_targets:

        baseline = baseline_corruption_test(
            fragments,
            target_index,
            original,
        )

        recovered = recovery_corruption_test(
            fragments,
            parity,
            target_index,
            original,
        )

        address = fragment_address(
            fragments[target_index]
        )

        print(
            f"{address} | "
            f"{baseline['exact']} | "
            f"{recovered['detected']} | "
            f"{recovered['recovered']} | "
            f"{recovered['exact']}"
        )

        rows.append(
            {
                "experiment": "corruption",
                "address": address,
                "baseline_exact": baseline[
                    "exact"
                ],
                "recovery_success": recovered[
                    "recovered"
                ],
                "final_exact": recovered[
                    "exact"
                ],
            }
        )

    # --------------------------------------------------------
    # Quantitative summary
    # --------------------------------------------------------

    total = len(rows)

    baseline_exact = sum(
        1
        for row in rows
        if row["baseline_exact"]
    )

    recovery_success = sum(
        1
        for row in rows
        if row["recovery_success"]
    )

    final_exact = sum(
        1
        for row in rows
        if row["final_exact"]
    )

    missing_count = sum(
        1
        for row in rows
        if row["experiment"]
        == "missing"
    )

    corruption_count = sum(
        1
        for row in rows
        if row["experiment"]
        == "corruption"
    )

    missing_recovered = sum(
        1
        for row in rows
        if row["experiment"] == "missing"
        and row["recovery_success"]
    )

    corruption_recovered = sum(
        1
        for row in rows
        if row["experiment"] == "corruption"
        and row["recovery_success"]
    )

    print("")
    print("QUANTITATIVE SUMMARY")
    print("-" * 60)

    print(
        f"Total controlled tests : "
        f"{total}"
    )

    print(
        f"Baseline exact         : "
        f"{baseline_exact}/{total}"
    )

    print(
        f"Recovered fragments    : "
        f"{recovery_success}/{total}"
    )

    print(
        f"Final exact files      : "
        f"{final_exact}/{total}"
    )

    print(
        f"Missing recovered      : "
        f"{missing_recovered}/{missing_count}"
    )

    print(
        f"Corruption recovered   : "
        f"{corruption_recovered}/{corruption_count}"
    )

    baseline_rate = (
        baseline_exact
        / total
        * 100
    )

    recovery_rate = (
        final_exact
        / total
        * 100
    )

    print(
        f"Baseline exact rate    : "
        f"{baseline_rate:.2f}%"
    )

    print(
        f"Recovery exact rate    : "
        f"{recovery_rate:.2f}%"
    )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    csv_path = (
        ROOT
        / "data"
        / "experiments"
        / "milestone9"
        / "baseline_vs_recovery.csv"
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "experiment",
                "address",
                "baseline_exact",
                "recovery_success",
                "final_exact",
            ],
        )

        writer.writeheader()

        writer.writerows(rows)

    print("")
    print("RESULT DATA")
    print("-" * 60)

    print(
        f"CSV saved to          : "
        f"{csv_path}"
    )

    # --------------------------------------------------------
    # Important scope statement
    # --------------------------------------------------------

    print("")
    print("EXPERIMENT LIMITATION")
    print("-" * 60)

    print(
        "Recovery uses one XOR parity fragment per group"
    )

    print(
        "of four data fragments."
    )

    print(
        "The comparison demonstrates recovery of one"
    )

    print(
        "missing or corrupted fragment per group."
    )

    print(
        "It does not demonstrate recovery from multiple"
    )

    print(
        "simultaneous losses in the same group."
    )

    print(
        "No physical DNA storage or physical DNA error-rate"
    )

    print(
        "claim is made by this simulation."
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    expected = (
        total == 10
        and baseline_exact == 0
        and missing_recovered == missing_count
        and corruption_recovered
        == corruption_count
        and final_exact == total
    )

    print("")
    print("=" * 60)

    if expected:

        print("RESULT: PASS")

        print(
            "Baseline failed under controlled fragment loss"
        )

        print(
            "and corruption as expected."
        )

        print(
            "Redundancy recovered every tested single"
        )

        print(
            "fragment failure."
        )

        print(
            "All recovered files matched the original"
        )

        print(
            "SHA-256 exactly."
        )

    else:

        print("RESULT: FAIL")

    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
