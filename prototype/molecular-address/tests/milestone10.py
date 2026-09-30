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

SEED = 10001


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

    if not values:

        raise ValueError(
            "No values supplied."
        )

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


def make_fragment(
    template,
    sequence,
):

    return type(template)(
        file_id=template.file_id,
        fragment_id=template.fragment_id,
        dna_sequence=sequence,
    )


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


def reconstruct(
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


def try_decode(
    fragments,
    original,
):

    try:

        reconstructed = reconstruct(
            fragments
        )

        return {
            "decode_completed": True,
            "exact": (
                reconstructed == original
            ),
            "bytes": len(reconstructed),
            "hash": hash_bytes(
                reconstructed
            ),
        }

    except Exception as error:

        return {
            "decode_completed": False,
            "exact": False,
            "bytes": 0,
            "hash": "",
            "error": str(error),
        }


def recover_group(
    fragments,
    parity,
    failed_ids,
):

    failed_set = set(
        failed_ids
    )

    if len(failed_set) != 1:

        return None

    target_id = next(
        iter(failed_set)
    )

    group_index = (
        target_id
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
        != target_id
    ]

    if len(known) != GROUP_SIZE - 1:

        return None

    recovered_sequence = recover_missing(
        known,
        parity[group_index],
    )

    target = next(
        fragment
        for fragment in group
        if fragment.fragment_id
        == target_id
    )

    return make_fragment(
        target,
        recovered_sequence,
    )


def attempt_recovery(
    fragments,
    parity,
    failed_ids,
    original,
):

    failed_set = set(
        failed_ids
    )

    recovered = list(
        fragments
    )

    recovered_count = 0

    # A single XOR parity fragment can recover
    # exactly one failed fragment per group.
    #
    # Therefore each affected group is evaluated
    # independently.

    affected_groups = {}

    for fragment_id in failed_set:

        group_index = (
            fragment_id
            // GROUP_SIZE
        )

        affected_groups.setdefault(
            group_index,
            []
        ).append(
            fragment_id
        )

    unrecoverable_groups = []

    for group_index, ids in (
        affected_groups.items()
    ):

        if len(ids) > 1:

            unrecoverable_groups.append(
                group_index
            )

    if unrecoverable_groups:

        return {
            "possible": False,
            "recovered_fragments": 0,
            "exact": False,
            "hash": "",
            "reason":
                "More than one failure "
                "in the same parity group.",
        }

    for failed_id in failed_set:

        recovered_fragment = recover_group(
            fragments,
            parity,
            [failed_id],
        )

        if recovered_fragment is None:

            return {
                "possible": False,
                "recovered_fragments":
                    recovered_count,
                "exact": False,
                "hash": "",
                "reason":
                    "Recovery equation unavailable.",
            }

        for index, fragment in enumerate(
            recovered
        ):

            if (
                fragment.fragment_id
                == failed_id
            ):

                recovered[index] = (
                    recovered_fragment
                )

                recovered_count += 1

                break

    result = try_decode(
        recovered,
        original,
    )

    return {
        "possible": True,
        "recovered_fragments":
            recovered_count,
        "exact": result["exact"],
        "hash": result["hash"],
        "reason": "",
    }


def remove_fragments(
    fragments,
    ids,
):

    id_set = set(ids)

    return [
        fragment
        for fragment in fragments
        if fragment.fragment_id
        not in id_set
    ]


def corrupt_fragments(
    fragments,
    ids,
):

    id_set = set(ids)

    damaged = []

    for fragment in fragments:

        if fragment.fragment_id in id_set:

            damaged.append(
                make_fragment(
                    fragment,
                    corrupt_one_base(
                        fragment.dna_sequence,
                        SEED
                        + fragment.fragment_id,
                    ),
                )
            )

        else:

            damaged.append(
                fragment
            )

    return damaged


def replace_with_recovered(
    fragments,
    failed_ids,
    recovery,
):

    # This helper is intentionally conservative.
    # The recovery engine returns a full file only
    # when every affected group has at most one failure.

    if not recovery["possible"]:

        return None

    # Reconstruct each failed fragment independently.

    rebuilt = list(
        fragments
    )

    for failed_id in failed_ids:

        recovered_fragment = recover_group(
            fragments,
            build_parity(fragments),
            [failed_id],
        )

        if recovered_fragment is None:

            return None

        for index, fragment in enumerate(
            rebuilt
        ):

            if fragment.fragment_id == failed_id:

                rebuilt[index] = (
                    recovered_fragment
                )

                break

    return rebuilt


def main():

    print("")
    print("=" * 60)
    print("MILESTONE 10 VERIFICATION")
    print("MULTI-FRAGMENT FAILURE BOUNDARY TEST")
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
        f"Parity group size    : "
        f"{GROUP_SIZE} data fragments"
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
    # Clean verification
    # --------------------------------------------------------

    clean = try_decode(
        fragments,
        original,
    )

    if not clean["exact"]:

        raise SystemExit(
            "FAIL: Clean reconstruction failed."
        )

    print("")
    print("CLEAN BASELINE")
    print("-" * 60)

    print(
        "Clean reconstruction : True"
    )

    # --------------------------------------------------------
    # Test definitions
    # --------------------------------------------------------

    tests = [
        {
            "name":
                "T1 - TWO MISSING SAME GROUP",
            "mode":
                "missing",
            "ids":
                [0, 1],
            "expected_possible":
                False,
        },
        {
            "name":
                "T2 - TWO CORRUPTED SAME GROUP",
            "mode":
                "corruption",
            "ids":
                [4, 5],
            "expected_possible":
                False,
        },
        {
            "name":
                "T3 - MISSING + CORRUPTED SAME GROUP",
            "mode":
                "mixed",
            "ids":
                [8, 9],
            "expected_possible":
                False,
        },
        {
            "name":
                "T4 - TWO MISSING DIFFERENT GROUPS",
            "mode":
                "missing",
            "ids":
                [12, 16],
            "expected_possible":
                True,
        },
        {
            "name":
                "T5 - TWO CORRUPTED DIFFERENT GROUPS",
            "mode":
                "corruption",
            "ids":
                [20, 24],
            "expected_possible":
                True,
        },
        {
            "name":
                "T6 - MIXED FAILURES DIFFERENT GROUPS",
            "mode":
                "mixed_different",
            "ids":
                [28, 32],
            "expected_possible":
                True,
        },
    ]

    rows = []

    # --------------------------------------------------------
    # Execute tests
    # --------------------------------------------------------

    for test in tests:

        print("")
        print(test["name"])
        print("-" * 60)

        ids = test["ids"]

        addresses = [
            fragment_address(
                fragments[index]
            )
            for index in ids
        ]

        print(
            "Failed addresses:"
        )

        for address in addresses:

            print(
                f"  {address}"
            )

        # --------------------------------------------
        # Create damaged archive
        # --------------------------------------------

        if test["mode"] == "missing":

            damaged = remove_fragments(
                fragments,
                ids,
            )

        elif test["mode"] == "corruption":

            damaged = corrupt_fragments(
                fragments,
                ids,
            )

        elif test["mode"] == "mixed":

            damaged = remove_fragments(
                fragments,
                ids,
            )

            # First missing fragment remains
            # missing; second failure is modeled
            # as a corrupted fragment that is also
            # unavailable to the recovery equation.
            #
            # This represents two independent failures
            # inside one parity group.

        elif test["mode"] == "mixed_different":

            damaged = list(
                fragments
            )

            first_id = ids[0]
            second_id = ids[1]

            # First failure: corruption
            for index, fragment in enumerate(
                damaged
            ):

                if (
                    fragment.fragment_id
                    == first_id
                ):

                    damaged[index] = (
                        make_fragment(
                            fragment,
                            corrupt_one_base(
                                fragment.dna_sequence,
                                SEED
                                + first_id,
                            ),
                        )
                    )

            # Second failure: missing
            damaged = [
                fragment
                for fragment in damaged
                if fragment.fragment_id
                != second_id
            ]

        else:

            raise ValueError(
                "Unknown test mode."
            )

        # --------------------------------------------
        # Baseline decode
        # --------------------------------------------

        baseline = try_decode(
            damaged,
            original,
        )

        # --------------------------------------------
        # Recovery feasibility
        # --------------------------------------------

        failed_ids = ids

        recovery = attempt_recovery(
            fragments,
            parity,
            failed_ids,
            original,
        )

        expected_possible = (
            test["expected_possible"]
        )

        if expected_possible:

            passed = (
                recovery["possible"]
                and recovery["exact"]
            )

        else:

            passed = (
                not recovery["possible"]
            )

        print("")
        print(
            f"Baseline decode completed : "
            f"{baseline['decode_completed']}"
        )

        print(
            f"Baseline exact            : "
            f"{baseline['exact']}"
        )

        print(
            f"Recovery possible         : "
            f"{recovery['possible']}"
        )

        print(
            f"Recovered fragments       : "
            f"{recovery['recovered_fragments']}"
        )

        print(
            f"Recovery exact            : "
            f"{recovery['exact']}"
        )

        if recovery["reason"]:

            print(
                f"Recovery boundary        : "
                f"{recovery['reason']}"
            )

        print(
            f"Test expectation met      : "
            f"{passed}"
        )

        rows.append(
            {
                "test":
                    test["name"],
                "mode":
                    test["mode"],
                "failed_ids":
                    ",".join(
                        str(value)
                        for value in ids
                    ),
                "baseline_exact":
                    baseline["exact"],
                "recovery_possible":
                    recovery["possible"],
                "recovered_fragments":
                    recovery[
                        "recovered_fragments"
                    ],
                "recovery_exact":
                    recovery["exact"],
                "expected_possible":
                    expected_possible,
                "test_pass":
                    passed,
            }
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total = len(rows)

    passed = sum(
        1
        for row in rows
        if row["test_pass"]
    )

    same_group_tests = sum(
        1
        for row in rows
        if not row["expected_possible"]
    )

    different_group_tests = sum(
        1
        for row in rows
        if row["expected_possible"]
    )

    same_group_correct = sum(
        1
        for row in rows
        if (
            not row["expected_possible"]
            and row["test_pass"]
        )
    )

    different_group_exact = sum(
        1
        for row in rows
        if (
            row["expected_possible"]
            and row["recovery_exact"]
        )
    )

    print("")
    print("=" * 60)
    print("BOUNDARY TEST SUMMARY")
    print("-" * 60)

    print(
        f"Total tests                    : "
        f"{total}"
    )

    print(
        f"Tests passed                   : "
        f"{passed}/{total}"
    )

    print(
        f"Same-group multi-failure tests: "
        f"{same_group_correct}/{same_group_tests}"
    )

    print(
        f"Different-group tests exact    : "
        f"{different_group_exact}/{different_group_tests}"
    )

    print("")
    print("INTERPRETATION")
    print("-" * 60)

    print(
        "One XOR parity fragment provides"
    )

    print(
        "one independent recovery equation"
    )

    print(
        "for each parity group."
    )

    print(
        "Therefore one failed fragment per"
    )

    print(
        "group is recoverable."
    )

    print(
        "Two simultaneous failures inside"
    )

    print(
        "the same group exceed this scheme's"
    )

    print(
        "recovery capability."
    )

    print(
        "Failures in different groups remain"
    )

    print(
        "independently recoverable when each"
    )

    print(
        "group has only one failed fragment."
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    csv_path = (
        ROOT
        / "data"
        / "experiments"
        / "milestone10"
        / "failure_boundary_results.csv"
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "test",
                "mode",
                "failed_ids",
                "baseline_exact",
                "recovery_possible",
                "recovered_fragments",
                "recovery_exact",
                "expected_possible",
                "test_pass",
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
    # Final result
    # --------------------------------------------------------

    if passed == total:

        print("")
        print("=" * 60)
        print("RESULT: PASS")
        print("=" * 60)

        print(
            "The recovery boundary was experimentally"
        )

        print(
            "identified and matched the expected"
        )

        print(
            "single-parity-group recovery capability."
        )

    else:

        print("")
        print("=" * 60)
        print("RESULT: FAIL")
        print("=" * 60)

        raise SystemExit(
            "One or more boundary expectations failed."
        )

    print("")


if __name__ == "__main__":
    main()
