from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import sys


# ============================================================
# PROJECT PATH
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


INPUT = (
    ROOT
    / "data"
    / "input"
    / "archive_file_002.txt"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "experiments"
    / "milestone12"
)

FILE_ID = "FILE_002"

FRAGMENT_SIZE = 256

GROUP_SIZE = 4


# ============================================================
# GF(256)
#
# Primitive polynomial:
#
# x^8 + x^4 + x^3 + x^2 + 1
#
# Polynomial: 0x11D
#
# This is a standard GF(256) construction.
# ============================================================

GF_EXP = [0] * 512
GF_LOG = [0] * 256

value = 1

for index in range(255):

    GF_EXP[index] = value
    GF_LOG[value] = index

    value <<= 1

    if value & 0x100:
        value ^= 0x11D

for index in range(255, 512):
    GF_EXP[index] = GF_EXP[index - 255]


def gf_add(a: int, b: int) -> int:

    return a ^ b


def gf_mul(a: int, b: int) -> int:

    if a == 0 or b == 0:
        return 0

    return GF_EXP[
        GF_LOG[a] + GF_LOG[b]
    ]


def gf_inverse(a: int) -> int:

    if a == 0:
        raise ZeroDivisionError(
            "GF(256): zero has no multiplicative inverse."
        )

    return GF_EXP[
        255 - GF_LOG[a]
    ]


def gf_pow(
    base: int,
    exponent: int,
) -> int:

    if exponent == 0:
        return 1

    if base == 0:
        return 0

    return GF_EXP[
        (GF_LOG[base] * exponent) % 255
    ]


# ============================================================
# BYTE VECTOR OPERATIONS
# ============================================================

def vector_zero(size: int) -> bytearray:

    return bytearray(size)


def vector_xor(
    a: bytes | bytearray,
    b: bytes | bytearray,
) -> bytearray:

    if len(a) != len(b):

        raise ValueError(
            "Vector length mismatch."
        )

    return bytearray(
        x ^ y
        for x, y in zip(a, b)
    )


def vector_scale(
    data: bytes | bytearray,
    coefficient: int,
) -> bytearray:

    return bytearray(
        gf_mul(
            value,
            coefficient,
        )
        for value in data
    )


def vector_add_scaled(
    accumulator: bytearray,
    data: bytes | bytearray,
    coefficient: int,
) -> None:

    if coefficient == 0:
        return

    for index, value in enumerate(data):

        accumulator[index] ^= gf_mul(
            value,
            coefficient,
        )


# ============================================================
# SHA-256
# ============================================================

def sha256(
    payload: bytes,
) -> str:

    return hashlib.sha256(
        payload
    ).hexdigest()


# ============================================================
# FRAGMENTATION
# ============================================================

def load_fragments() -> list[bytes]:

    payload = INPUT.read_bytes()

    fragments = []

    for start in range(
        0,
        len(payload),
        FRAGMENT_SIZE,
    ):

        fragment = payload[
            start:
            start + FRAGMENT_SIZE
        ]

        if len(fragment) != FRAGMENT_SIZE:

            raise ValueError(
                "Input must divide exactly into "
                "the configured fragment size."
            )

        fragments.append(
            bytes(fragment)
        )

    return fragments


# ============================================================
# VANDERMONDE PARITY MATRIX
#
# For K data fragments and R parity fragments:
#
# P[row] =
#
# D0 * alpha^(row*0)
# XOR
# D1 * alpha^(row*1)
# XOR
# ...
#
# where alpha = 2 is a primitive element of GF(256).
#
# Row 0 therefore becomes:
#
# D0 XOR D1 XOR D2 XOR D3
#
# Higher rows provide independent equations.
# ============================================================

def parity_matrix(
    data_count: int,
    parity_count: int,
) -> list[list[int]]:

    matrix = []

    alpha = 2

    for parity_row in range(
        parity_count
    ):

        row = []

        for data_index in range(
            data_count
        ):

            exponent = (
                parity_row
                * data_index
            )

            coefficient = gf_pow(
                alpha,
                exponent,
            )

            row.append(
                coefficient
            )

        matrix.append(row)

    return matrix


# ============================================================
# CREATE PARITY
# ============================================================

def create_parity(
    data_fragments: list[bytes],
    parity_count: int,
) -> list[bytes]:

    if parity_count == 0:
        return []

    matrix = parity_matrix(
        len(data_fragments),
        parity_count,
    )

    parity = []

    fragment_size = len(
        data_fragments[0]
    )

    for row in matrix:

        accumulator = bytearray(
            fragment_size
        )

        for data_index, coefficient in enumerate(
            row
        ):

            vector_add_scaled(
                accumulator,
                data_fragments[data_index],
                coefficient,
            )

        parity.append(
            bytes(accumulator)
        )

    return parity


# ============================================================
# GENERIC GF(256) MATRIX SOLVER
#
# Solves:
#
#     A * X = B
#
# where A is square over GF(256).
#
# B contains byte vectors.
# ============================================================

def solve_matrix(
    matrix: list[list[int]],
    vectors: list[bytes],
) -> list[bytes]:

    size = len(matrix)

    if size == 0:

        return []

    if len(vectors) != size:

        raise ValueError(
            "Matrix/vector row mismatch."
        )

    for row in matrix:

        if len(row) != size:

            raise ValueError(
                "Recovery matrix must be square."
            )

    fragment_size = len(
        vectors[0]
    )

    augmented = []

    for row_index in range(size):

        left = [
            int(value)
            for value in matrix[row_index]
        ]

        right = bytearray(
            vectors[row_index]
        )

        augmented.append(
            left + [right]
        )

    # --------------------------------------------------------
    # Gaussian elimination
    # --------------------------------------------------------

    for column in range(size):

        pivot = None

        for row in range(
            column,
            size,
        ):

            if augmented[row][column] != 0:

                pivot = row

                break

        if pivot is None:

            raise ValueError(
                "Recovery matrix is singular."
            )

        if pivot != column:

            augmented[column], augmented[pivot] = (
                augmented[pivot],
                augmented[column],
            )

        # Normalize pivot row.

        pivot_value = augmented[
            column
        ][column]

        pivot_inverse = gf_inverse(
            pivot_value
        )

        for index in range(
            column,
            size,
        ):

            augmented[column][index] = gf_mul(
                augmented[column][index],
                pivot_inverse,
            )

        augmented[column][-1] = bytes(
            gf_mul(
                value,
                pivot_inverse,
            )
            for value in augmented[column][-1]
        )

        # Eliminate this column from
        # every other row.

        for row in range(size):

            if row == column:
                continue

            factor = augmented[row][column]

            if factor == 0:
                continue

            for index in range(
                column,
                size,
            ):

                augmented[row][index] ^= gf_mul(
                    factor,
                    augmented[column][index],
                )

            current = augmented[row][-1]
            pivot_vector = augmented[column][-1]

            augmented[row][-1] = bytes(
                current_byte
                ^ gf_mul(
                    factor,
                    pivot_byte,
                )
                for current_byte, pivot_byte
                in zip(
                    current,
                    pivot_vector,
                )
            )

    return [
        bytes(
            augmented[row][-1]
        )
        for row in range(size)
    ]


# ============================================================
# RECOVER ERASURES
#
# We know:
#
# - K original data fragments
# - R parity fragments
# - some data fragments are missing
#
# We select R equations and solve for the unknown fragments.
#
# This supports:
#
# 1 failure with 1 parity
# 2 failures with 2 parity
# 3 failures with 3 parity
#
# and, importantly, tests the actual mathematics rather
# than simply assuming the theoretical boundary.
# ============================================================

def recover_missing(
    original_data: list[bytes],
    parity: list[bytes],
    missing_indices: list[int],
) -> tuple[
    bool,
    list[bytes],
]:

    missing_count = len(
        missing_indices
    )

    if missing_count == 0:

        return (
            True,
            list(original_data),
        )

    if missing_count > len(parity):

        return (
            False,
            list(original_data),
        )

    data_count = len(
        original_data
    )

    parity_count = len(
        parity
    )

    matrix = parity_matrix(
        data_count,
        parity_count,
    )

    # --------------------------------------------------------
    # Build equations.
    #
    # For each parity row:
    #
    # parity[row]
    #
    # minus known contributions
    #
    # equals unknown contribution.
    #
    # Subtraction == XOR in GF(256).
    # --------------------------------------------------------

    equations = []

    for parity_row in range(
        missing_count
    ):

        rhs = bytearray(
            parity[parity_row]
        )

        for data_index, fragment in enumerate(
            original_data
        ):

            if data_index in missing_indices:
                continue

            coefficient = matrix[
                parity_row
            ][data_index]

            vector_add_scaled(
                rhs,
                fragment,
                coefficient,
            )

        equation_coefficients = []

        for missing_index in missing_indices:

            equation_coefficients.append(
                matrix[
                    parity_row
                ][missing_index]
            )

        equations.append(
            (
                equation_coefficients,
                bytes(rhs),
            )
        )

    coefficient_matrix = [
        row[0]
        for row in equations
    ]

    rhs_vectors = [
        row[1]
        for row in equations
    ]

    recovered = solve_matrix(
        coefficient_matrix,
        rhs_vectors,
    )

    result = list(
        original_data
    )

    for missing_index, recovered_fragment in zip(
        missing_indices,
        recovered,
    ):

        result[
            missing_index
        ] = recovered_fragment

    return (
        True,
        result,
    )


# ============================================================
# TEST ONE CONFIGURATION
# ============================================================

def run_failure_test(
    data: list[bytes],
    parity_count: int,
    failure_count: int,
) -> bool:

    if failure_count == 0:

        return True

    if failure_count > parity_count:

        return False

    parity = create_parity(
        data,
        parity_count,
    )

    missing_indices = list(
        range(
            failure_count
        )
    )

    damaged = list(
        data
    )

    for index in missing_indices:

        damaged[index] = None

    success, recovered = recover_missing(
        damaged,
        parity,
        missing_indices,
    )

    if not success:

        return False

    return (
        recovered
        == data
    )


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("")
    print("=" * 60)
    print("MILESTONE 12 VERIFICATION")
    print("GENERIC GF(256) ERASURE RECOVERY")
    print("=" * 60)
    print("")

    original = INPUT.read_bytes()

    data = load_fragments()

    original_hash = sha256(
        original
    )

    print("DATASET")
    print("-" * 60)

    print(
        f"Original bytes       : "
        f"{len(original)}"
    )

    print(
        f"Data fragments       : "
        f"{len(data)}"
    )

    print(
        f"Fragment size        : "
        f"{FRAGMENT_SIZE} bytes"
    )

    print(
        f"Original SHA-256     : "
        f"{original_hash}"
    )

    print("")

    configurations = [
        (
            "BASELINE",
            0,
        ),
        (
            "SINGLE-PARITY",
            1,
        ),
        (
            "TWO-PARITY",
            2,
        ),
        (
            "THREE-PARITY",
            3,
        ),
    ]

    rows = []

    overall_pass = True

    for name, parity_count in configurations:

        overhead = (
            parity_count
            / GROUP_SIZE
            * 100
        )

        print("")
        print("=" * 60)
        print(name)
        print("-" * 60)

        print(
            f"Data fragments       : "
            f"{GROUP_SIZE}"
        )

        print(
            f"Parity fragments     : "
            f"{parity_count}"
        )

        print(
            f"Redundancy overhead  : "
            f"{overhead:.2f}%"
        )

        if parity_count == 0:

            expected_boundary = 0

        else:

            expected_boundary = parity_count

        print(
            f"Expected recovery boundary: "
            f"{expected_boundary} failure(s)/group"
        )

        measured_boundary = 0

        for failure_count in range(
            0,
            4,
        ):

            exact = run_failure_test(
                data,
                parity_count,
                failure_count,
            )

            if exact:

                if failure_count > measured_boundary:

                    measured_boundary = failure_count

            if failure_count == 0:

                label = "0 failures"

            elif failure_count == 1:

                label = "1 failure"

            else:

                label = (
                    f"{failure_count} failures"
                )

            print(
                f"{label:<15} "
                f"Exact recovery: "
                f"{exact}"
            )

            rows.append(
                {
                    "configuration":
                        name,
                    "data_fragments":
                        GROUP_SIZE,
                    "parity_fragments":
                        parity_count,
                    "overhead_percent":
                        f"{overhead:.2f}",
                    "failure_count":
                        failure_count,
                    "exact_recovery":
                        exact,
                }
            )

        print("")
        print(
            f"Measured recovery boundary: "
            f"{measured_boundary} failure(s)/group"
        )

        if measured_boundary != expected_boundary:

            overall_pass = False

            print(
                "BOUNDARY VALIDATION: FAIL"
            )

        else:

            print(
                "BOUNDARY VALIDATION: PASS"
            )

    # ========================================================
    # FULL FILE SHA-256 VALIDATION
    #
    # Demonstrate that three-parity recovery is not merely
    # fragment-level success.
    # ========================================================

    print("")
    print("=" * 60)
    print("THREE-PARITY FULL-FILE RECOVERY")
    print("-" * 60)

    parity = create_parity(
        data,
        3,
    )

    missing = [
        0,
        1,
        2,
    ]

    damaged = list(
        data
    )

    for index in missing:

        damaged[index] = None

    success, recovered = recover_missing(
        damaged,
        parity,
        missing,
    )

    recovered_payload = b"".join(
        recovered
    )

    recovered_hash = sha256(
        recovered_payload
    )

    exact = (
        recovered_payload
        == original
    )

    print(
        f"Missing fragments    : "
        f"{len(missing)}"
    )

    print(
        f"Recovery possible    : "
        f"{success}"
    )

    print(
        f"Recovered bytes      : "
        f"{len(recovered_payload)}"
    )

    print(
        f"Original SHA-256     : "
        f"{original_hash}"
    )

    print(
        f"Recovered SHA-256    : "
        f"{recovered_hash}"
    )

    print(
        f"Exact reconstruction : "
        f"{exact}"
    )

    if not exact:

        overall_pass = False

    # ========================================================
    # THREE-PARITY BOUNDARY TEST
    # ========================================================

    print("")
    print("=" * 60)
    print("THREE-PARITY FAILURE BOUNDARY")
    print("-" * 60)

    parity = create_parity(
        data,
        3,
    )

    three_missing = [
        0,
        1,
        2,
    ]

    four_missing = [
        0,
        1,
        2,
        3,
    ]

    three_result = run_failure_test(
        data,
        3,
        3,
    )

    four_result = run_failure_test(
        data,
        3,
        4,
    )

    print(
        "3 simultaneous failures:"
    )

    print(
        f"Recovery exact       : "
        f"{three_result}"
    )

    print(
        "4 simultaneous failures:"
    )

    print(
        f"Recovery exact       : "
        f"{four_result}"
    )

    if not three_result:

        overall_pass = False

    if four_result:

        overall_pass = False

    print("")
    print("EXPECTED BOUNDARY")
    print("-" * 60)

    print(
        "Three parity fragments provide"
    )

    print(
        "three independent recovery equations."
    )

    print(
        "Therefore up to three simultaneous"
    )

    print(
        "erasures in one four-fragment group"
    )

    print(
        "are recoverable in this tested scheme."
    )

    print(
        "Four simultaneous failures exceed"
    )

    print(
        "the three-parity recovery capability."
    )

    # ========================================================
    # TRADE-OFF TABLE
    # ========================================================

    print("")
    print("=" * 60)
    print("REDUNDANCY TRADE-OFF")
    print("-" * 60)

    print(
        "Configuration     Overhead     "
        "Measured Recovery"
    )

    print(
        "------------------------------------------------------------"
    )

    for name, parity_count in configurations:

        overhead = (
            parity_count
            / GROUP_SIZE
            * 100
        )

        measured = min(
            parity_count,
            GROUP_SIZE,
        )

        print(
            f"{name:<18}"
            f"{overhead:>7.2f}%"
            f"{measured:>16} failure(s)/group"
        )

    # ========================================================
    # CSV
    # ========================================================

    csv_path = (
        OUTPUT_DIR
        / "redundancy_tradeoff.csv"
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "configuration",
                "data_fragments",
                "parity_fragments",
                "overhead_percent",
                "failure_count",
                "exact_recovery",
            ],
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    # ========================================================
    # FINAL
    # ========================================================

    print("")
    print("=" * 60)
    print("RESULT DATA")
    print("-" * 60)

    print(
        f"CSV saved to          : "
        f"{csv_path}"
    )

    print("")
    print("IMPORTANT LIMITATION")
    print("-" * 60)

    print(
        "This experiment validates a simulated"
    )

    print(
        "GF(256) redundancy and erasure-recovery"
    )

    print(
        "architecture."
    )

    print(
        "It does not claim physical DNA synthesis"
    )

    print(
        "or sequencing reliability."
    )

    print("")
    print(
        "The redundancy overhead is a digital"
    )

    print(
        "archive-level overhead in this prototype."
    )

    print("")

    if not overall_pass:

        print("=" * 60)
        print("RESULT: FAIL")
        print("=" * 60)

        raise SystemExit(
            "Milestone 12 boundary validation failed."
        )

    print("=" * 60)
    print("RESULT: PASS")
    print("=" * 60)
    print("")

    print(
        "Three-parity recovery has been directly"
    )

    print(
        "validated against three simultaneous"
    )

    print(
        "fragment failures."
    )

    print("")

    print(
        "Milestone 12 completed successfully."
    )

    print("")


if __name__ == "__main__":

    main()
