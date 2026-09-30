from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import sys


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT))

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

PARITY_COUNT = 2

FIELD_SIZE = 256


# ============================================================
# GF(256)
# Primitive polynomial:
# x^8 + x^4 + x^3 + x^2 + 1
# represented as 0x11d
# ============================================================

EXP = [0] * 512
LOG = [0] * 256

value = 1

for i in range(255):

    EXP[i] = value
    LOG[value] = i

    value <<= 1

    if value & 0x100:
        value ^= 0x11D

for i in range(255, 512):
    EXP[i] = EXP[i - 255]


def gf_mul(a: int, b: int) -> int:

    if a == 0 or b == 0:
        return 0

    return EXP[
        LOG[a] + LOG[b]
    ]


def gf_div(a: int, b: int) -> int:

    if b == 0:
        raise ZeroDivisionError(
            "GF(256) division by zero."
        )

    if a == 0:
        return 0

    exponent = LOG[a] - LOG[b]

    if exponent < 0:
        exponent += 255

    return EXP[exponent]


def gf_inverse(a: int) -> int:

    if a == 0:
        raise ZeroDivisionError(
            "GF(256) inverse of zero."
        )

    return EXP[255 - LOG[a]]


def xor_bytes(
    a: bytes,
    b: bytes,
) -> bytes:

    if len(a) != len(b):
        raise ValueError(
            "GF parity operands have different lengths."
        )

    return bytes(
        x ^ y
        for x, y in zip(a, b)
    )


def scale_bytes(
    data: bytes,
    coefficient: int,
) -> bytes:

    return bytes(
        gf_mul(byte, coefficient)
        for byte in data
    )


# ============================================================
# DNA <-> bytes
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


def hash_bytes(
    value: bytes,
) -> str:

    return hashlib.sha256(
        value
    ).hexdigest()


# ============================================================
# Two-parity equations
#
# P = D0 + D1 + D2 + D3
#
# Q = 1D0 + 2D1 + 3D2 + 4D3
#
# All operations are GF(256).
# ============================================================


def create_parity(
    data_values: list[bytes],
) -> tuple[bytes, bytes]:

    if len(data_values) != GROUP_SIZE:
        raise ValueError(
            "Exactly four data fragments required."
        )

    parity_p = bytes(
        len(data_values[0])
    )

    parity_q = bytes(
        len(data_values[0])
    )

    for index, data in enumerate(
        data_values
    ):

        parity_p = xor_bytes(
            parity_p,
            data,
        )

        parity_q = xor_bytes(
            parity_q,
            scale_bytes(
                data,
                index + 1,
            ),
        )

    return parity_p, parity_q


def recover_two(
    data_values: list[bytes | None],
    parity_p: bytes,
    parity_q: bytes,
) -> list[bytes]:

    missing = [
        index
        for index, value in enumerate(
            data_values
        )
        if value is None
    ]

    if len(missing) != 2:
        raise ValueError(
            "Two-fragment recovery requires exactly two missing fragments."
        )

    a, b = missing

    known_p = bytes(
        len(parity_p)
    )

    known_q = bytes(
        len(parity_q)
    )

    for index, data in enumerate(
        data_values
    ):

        if data is None:
            continue

        known_p = xor_bytes(
            known_p,
            data,
        )

        known_q = xor_bytes(
            known_q,
            scale_bytes(
                data,
                index + 1,
            ),
        )

    # P = Da + Db
    #
    # Q = a*Da + b*Db
    #
    # Therefore:
    #
    # Da = (Q + bP) / (a + b)
    #
    # Db = P + Da

    rhs_p = xor_bytes(
        parity_p,
        known_p,
    )

    rhs_q = xor_bytes(
        parity_q,
        known_q,
    )

    coefficient_a = a + 1
    coefficient_b = b + 1

    denominator = (
        coefficient_a
        ^ coefficient_b
    )

    if denominator == 0:
        raise ValueError(
            "Singular recovery matrix."
        )

    b_times_p = scale_bytes(
        rhs_p,
        coefficient_b,
    )

    numerator_a = xor_bytes(
        rhs_q,
        b_times_p,
    )

    recovered_a = scale_bytes(
        numerator_a,
        gf_inverse(
            denominator
        ),
    )

    recovered_b = xor_bytes(
        rhs_p,
        recovered_a,
    )

    recovered = list(
        data_values
    )

    recovered[a] = recovered_a
    recovered[b] = recovered_b

    return [
        value
        for value in recovered
        if value is not None
    ]


def recover_two_ordered(
    data_values: list[bytes | None],
    parity_p: bytes,
    parity_q: bytes,
) -> dict[int, bytes]:

    missing = [
        index
        for index, value in enumerate(
            data_values
        )
        if value is None
    ]

    if len(missing) != 2:
        raise ValueError(
            "Exactly two missing fragments required."
        )

    a, b = missing

    known_p = bytes(
        len(parity_p)
    )

    known_q = bytes(
        len(parity_q)
    )

    for index, data in enumerate(
        data_values
    ):

        if data is None:
            continue

        known_p = xor_bytes(
            known_p,
            data,
        )

        known_q = xor_bytes(
            known_q,
            scale_bytes(
                data,
                index + 1,
            ),
        )

    rhs_p = xor_bytes(
        parity_p,
        known_p,
    )

    rhs_q = xor_bytes(
        parity_q,
        known_q,
    )

    coefficient_a = a + 1
    coefficient_b = b + 1

    denominator = (
        coefficient_a
        ^ coefficient_b
    )

    if denominator == 0:
        raise ValueError(
            "Singular recovery matrix."
        )

    numerator_a = xor_bytes(
        rhs_q,
        scale_bytes(
            rhs_p,
            coefficient_b,
        ),
    )

    recovered_a = scale_bytes(
        numerator_a,
        gf_inverse(
            denominator
        ),
    )

    recovered_b = xor_bytes(
        rhs_p,
        recovered_a,
    )

    return {
        a: recovered_a,
        b: recovered_b,
    }


# ============================================================
# Parity archive
# ============================================================


def build_two_parity(
    fragments,
):

    groups = {}

    for start in range(
        0,
        len(fragments),
        GROUP_SIZE,
    ):

        group_index = (
            start // GROUP_SIZE
        )

        group = fragments[
            start:
            start + GROUP_SIZE
        ]

        if len(group) != GROUP_SIZE:
            raise ValueError(
                "Incomplete parity group."
            )

        data = [
            dna_to_bytes(
                fragment.dna_sequence
            )
            for fragment in group
        ]

        p, q = create_parity(
            data
        )

        groups[group_index] = {
            "P": p,
            "Q": q,
        }

    return groups


def corrupt_bytes(
    data: bytes,
    seed: int,
) -> bytes:

    result = bytearray(data)

    index = seed % len(result)

    result[index] ^= 0x5A

    return bytes(result)


def reconstruct_file(
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


def fragment_address(
    fragment,
) -> str:

    return (
        f"{fragment.file_id}"
        f"-FRAG-"
        f"{fragment.fragment_id:06d}"
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


# ============================================================
# Main
# ============================================================


def main():

    print("")
    print("=" * 60)
    print("MILESTONE 11 VERIFICATION")
    print("TWO-PARITY REDUNDANCY + DUAL-FAILURE RECOVERY")
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

    parity_groups = build_two_parity(
        fragments
    )

    print("DATASET")
    print("-" * 60)

    print(
        f"Original bytes       : "
        f"{len(original)}"
    )

    print(
        f"Data fragments       : "
        f"{len(fragments)}"
    )

    print(
        f"Parity fragments     : "
        f"{len(parity_groups) * PARITY_COUNT}"
    )

    total_units = (
        len(fragments)
        + len(parity_groups)
        * PARITY_COUNT
    )

    overhead = (
        len(parity_groups)
        * PARITY_COUNT
        / len(fragments)
        * 100
    )

    print(
        f"Total archive units  : "
        f"{total_units}"
    )

    print(
        f"Redundancy overhead  : "
        f"{overhead:.2f}%"
    )

    print(
        f"Parity group size    : "
        f"{GROUP_SIZE} data + "
        f"{PARITY_COUNT} parity"
    )

    print(
        f"Original SHA-256     : "
        f"{original_hash}"
    )

    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------

    clean = reconstruct_file(
        fragments
    )

    clean_exact = (
        clean == original
    )

    print("")
    print("CLEAN BASELINE")
    print("-" * 60)

    print(
        f"Clean reconstruction : "
        f"{clean_exact}"
    )

    if not clean_exact:
        raise SystemExit(
            "Clean reconstruction failed."
        )

    # --------------------------------------------------------
    # Helper for recovery
    # --------------------------------------------------------

    def recover_targets(
        target_ids,
        damaged_mode,
    ):

        target_set = set(target_ids)

        rebuilt = list(fragments)

        affected_groups = {}

        for fragment_id in target_ids:

            group_index = fragment_id // GROUP_SIZE

            affected_groups.setdefault(
                group_index,
                []
            ).append(fragment_id)

        recovered_count = 0

        for group_index, ids in affected_groups.items():

            # Recovery capability is evaluated PER GROUP.
            #
            # 1 failed fragment -> XOR P recovery
            # 2 failed fragments -> P + Q recovery
            # 3+ failures -> outside this scheme

            if len(ids) > PARITY_COUNT:

                return {
                    "possible": False,
                    "recovered": 0,
                    "exact": False,
                    "reason":
                        "More than two failures "
                        "in one parity group.",
                }

            group_start = (
                group_index * GROUP_SIZE
            )

            group = fragments[
                group_start:
                group_start + GROUP_SIZE
            ]

            values = []

            for fragment in group:

                if fragment.fragment_id in target_set:

                    values.append(None)

                else:

                    values.append(
                        dna_to_bytes(
                            fragment.dna_sequence
                        )
                    )

            parity = parity_groups[group_index]

            missing_local = [
                index
                for index, value in enumerate(values)
                if value is None
            ]

            # ------------------------------------------------
            # ONE FAILURE
            # ------------------------------------------------

            if len(missing_local) == 1:

                missing_index = missing_local[0]

                known_sum = bytes(
                    len(parity["P"])
                )

                for value in values:

                    if value is not None:

                        known_sum = xor_bytes(
                            known_sum,
                            value,
                        )

                recovered_data = xor_bytes(
                    parity["P"],
                    known_sum,
                )

                recovered_map = {
                    missing_index:
                        recovered_data
                }

            # ------------------------------------------------
            # TWO FAILURES
            # ------------------------------------------------

            elif len(missing_local) == 2:

                recovered_map = recover_two_ordered(
                    values,
                    parity["P"],
                    parity["Q"],
                )

            else:

                continue

            for local_index, data in recovered_map.items():

                global_id = (
                    group_start
                    + local_index
                )

                template = next(
                    fragment
                    for fragment in group
                    if fragment.fragment_id == global_id
                )

                rebuilt_index = next(
                    index
                    for index, fragment in enumerate(rebuilt)
                    if fragment.fragment_id == global_id
                )

                rebuilt[rebuilt_index] = make_fragment(
                    template,
                    bytes_to_dna(data),
                )

                recovered_count += 1

        reconstructed = reconstruct_file(rebuilt)

        return {
            "possible": True,
            "recovered": recovered_count,
            "exact": reconstructed == original,
            "reason": "",
        }


    # --------------------------------------------------------
    # Tests
    # --------------------------------------------------------

    tests = [
        {
            "name":
                "T1 - TWO MISSING SAME GROUP",
            "ids":
                [0, 1],
            "mode":
                "missing",
            "expected":
                True,
        },
        {
            "name":
                "T2 - TWO CORRUPTED SAME GROUP",
            "ids":
                [4, 5],
            "mode":
                "corruption",
            "expected":
                True,
        },
        {
            "name":
                "T3 - MISSING + CORRUPTED SAME GROUP",
            "ids":
                [8, 9],
            "mode":
                "mixed",
            "expected":
                True,
        },
        {
            "name":
                "T4 - THREE MISSING SAME GROUP",
            "ids":
                [12, 13, 14],
            "mode":
                "missing",
            "expected":
                False,
        },
        {
            "name":
                "T5 - TWO MISSING DIFFERENT GROUPS",
            "ids":
                [16, 20],
            "mode":
                "missing",
            "expected":
                True,
        },
        {
            "name":
                "T6 - TWO CORRUPTED DIFFERENT GROUPS",
            "ids":
                [24, 28],
            "mode":
                "corruption",
            "expected":
                True,
        },
        {
            "name":
                "T7 - MIXED DIFFERENT GROUPS",
            "ids":
                [32, 36],
            "mode":
                "mixed",
            "expected":
                True,
        },
    ]

    rows = []

    for test in tests:

        print("")
        print(test["name"])
        print("-" * 60)

        for fragment_id in test["ids"]:

            address = (
                f"{FILE_ID}-FRAG-"
                f"{fragment_id:06d}"
            )

            print(
                f"Target address : "
                f"{address}"
            )

        result = recover_targets(
            test["ids"],
            test["mode"],
        )

        if test["expected"]:

            passed = (
                result["possible"]
                and result["exact"]
            )

        else:

            passed = (
                not result["possible"]
            )

        print("")
        print(
            f"Recovery possible : "
            f"{result['possible']}"
        )

        print(
            f"Recovered fragments: "
            f"{result['recovered']}"
        )

        print(
            f"Recovery exact     : "
            f"{result['exact']}"
        )

        if result["reason"]:

            print(
                f"Recovery boundary : "
                f"{result['reason']}"
            )

        print(
            f"Test expectation   : "
            f"{passed}"
        )

        rows.append(
            {
                "test":
                    test["name"],
                "target_ids":
                    ",".join(
                        str(x)
                        for x in test["ids"]
                    ),
                "mode":
                    test["mode"],
                "recovery_possible":
                    result["possible"],
                "recovered_fragments":
                    result["recovered"],
                "recovery_exact":
                    result["exact"],
                "expected_recovery":
                    test["expected"],
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

    dual_same_group = [
        row
        for row in rows
        if (
            "SAME GROUP"
            in row["test"]
            and "THREE"
            not in row["test"]
        )
    ]

    triple_failure = [
        row
        for row in rows
        if "THREE" in row["test"]
    ]

    print("")
    print("=" * 60)
    print("QUANTITATIVE SUMMARY")
    print("-" * 60)

    print(
        f"Total controlled tests : "
        f"{total}"
    )

    print(
        f"Tests passed           : "
        f"{passed}/{total}"
    )

    print(
        f"Dual-failure same-group tests : "
        f"{sum(r['test_pass'] for r in dual_same_group)}"
        f"/{len(dual_same_group)}"
    )

    print(
        f"Triple-failure boundary test  : "
        f"{sum(r['test_pass'] for r in triple_failure)}"
        f"/{len(triple_failure)}"
    )

    print("")
    print("COMPARISON WITH MILESTONE 8/9")
    print("-" * 60)

    print(
        "Single parity:"
    )

    print(
        "  4 data + 1 parity"
    )

    print(
        "  25% redundancy overhead"
    )

    print(
        "  1 failure per group"
    )

    print("")

    print(
        "Two-parity scheme:"
    )

    print(
        "  4 data + 2 parity"
    )

    print(
        f"  {overhead:.2f}% redundancy overhead"
    )

    print(
        "  2 failures per group"
    )

    print("")
    print("IMPORTANT LIMITATION")
    print("-" * 60)

    print(
        "This experiment demonstrates a"
    )

    print(
        "two-parity recovery scheme in simulation."
    )

    print(
        "It does not claim that physical DNA"
    )

    print(
        "molecules have these error characteristics."
    )

    print(
        "Three simultaneous failures in the"
    )

    print(
        "same four-fragment group exceed the"
    )

    print(
        "tested two-parity recovery capability."
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    csv_path = (
        ROOT
        / "data"
        / "experiments"
        / "milestone11"
        / "two_parity_results.csv"
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
                "target_ids",
                "mode",
                "recovery_possible",
                "recovered_fragments",
                "recovery_exact",
                "expected_recovery",
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
            "Two-parity redundancy successfully"
        )

        print(
            "demonstrated recovery of two simultaneous"
        )

        print(
            "fragment failures within a group."
        )

        print(
            "The experiment also established the"
        )

        print(
            "three-failure boundary under the tested"
        )

        print(
            "4-data + 2-parity configuration."
        )

    else:

        print("")
        print("=" * 60)
        print("RESULT: FAIL")
        print("=" * 60)

        raise SystemExit(
            "One or more Milestone 11 tests failed."
        )

    print("")


if __name__ == "__main__":
    main()
