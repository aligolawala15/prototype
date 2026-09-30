from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import sys


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT),
)


from app.dna_archive.archive import (
    encode_file_to_dna_fragments,
)

from app.errors.injector import (
    substitute_bases,
    insert_bases,
    delete_bases,
    delete_fragments,
)

from app.retrieval.measurement import (
    retrieve_and_measure,
)


# ============================================================
# Configuration
# ============================================================

INPUT = (
    ROOT
    / "data"
    / "input"
    / "archive_file_002.txt"
)

FILE_ID = "FILE_002"

FRAGMENT_SIZE = 256

SEED = 42

OUTPUT = (
    ROOT
    / "data"
    / "experiments"
    / "milestone6"
    / "error_rate_results.csv"
)


# ============================================================
# Experimental rates
# ============================================================

SUBSTITUTION_RATES = [
    0.0,
    0.0001,
    0.0005,
    0.001,
    0.0025,
    0.005,
    0.01,
]

INSERTION_RATES = [
    0.0,
    0.0001,
    0.0005,
    0.001,
    0.0025,
    0.005,
    0.01,
]

DELETION_RATES = [
    0.0,
    0.0001,
    0.0005,
    0.001,
    0.0025,
    0.005,
    0.01,
]

MISSING_FRAGMENT_RATES = [
    0.0,
    0.02,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
]


# ============================================================
# Helpers
# ============================================================

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_case(
    error_type: str,
    rate: float,
    clean_fragments,
    original: bytes,
    expected_fragments: int,
):
    """
    Run one deterministic corruption experiment.
    """

    if error_type == "substitution":

        corrupted, report = substitute_bases(
            clean_fragments,
            error_rate=rate,
            seed=SEED,
        )

    elif error_type == "insertion":

        corrupted, report = insert_bases(
            clean_fragments,
            error_rate=rate,
            seed=SEED,
        )

    elif error_type == "deletion":

        corrupted, report = delete_bases(
            clean_fragments,
            error_rate=rate,
            seed=SEED,
        )

    elif error_type == "missing_fragment":

        corrupted, report = delete_fragments(
            clean_fragments,
            fraction=rate,
            seed=SEED,
        )

    else:
        raise ValueError(
            f"Unknown error type: {error_type}"
        )

    result = retrieve_and_measure(
        corrupted,
        FILE_ID,
        expected_fragments,
        original,
    )

    return {
        "error_type": error_type,
        "requested_rate": rate,
        "affected_fragments": report.affected_fragments,
        "affected_bases": report.affected_bases,
        "deleted_fragments": report.deleted_fragments,
        "expected_fragments": expected_fragments,
        "retrieved_fragments": result.retrieved_fragments,
        "reconstructed_bytes": result.reconstructed_bytes,
        "original_bytes": len(original),
        "retrieval_complete": (
            result.retrieved_fragments
            == expected_fragments
        ),
        "exact_reconstruction": (
            result.reconstruction_success
        ),
        "decoding_error": (
            result.decoding_error or ""
        ),
    }


# ============================================================
# Main experiment
# ============================================================

def main():

    print("")
    print("=" * 60)
    print("MILESTONE 6 VERIFICATION")
    print("SYSTEMATIC DNA ERROR-RATE SWEEP")
    print("=" * 60)
    print("")

    # --------------------------------------------------------
    # Load original file
    # --------------------------------------------------------

    original = INPUT.read_bytes()

    original_hash = sha256(original)

    # --------------------------------------------------------
    # Generate clean DNA fragments once
    # --------------------------------------------------------

    clean_fragments = encode_file_to_dna_fragments(
        INPUT,
        file_id=FILE_ID,
        fragment_size=FRAGMENT_SIZE,
    )

    expected_fragments = len(clean_fragments)

    print("DATASET")
    print("-" * 60)

    print(
        f"Input file           : {INPUT}"
    )

    print(
        f"Original bytes       : {len(original)}"
    )

    print(
        f"DNA fragments        : {expected_fragments}"
    )

    print(
        f"Original SHA-256     : {original_hash}"
    )

    print("")

    # --------------------------------------------------------
    # Create experiment cases
    # --------------------------------------------------------

    cases = []

    for rate in SUBSTITUTION_RATES:
        cases.append(
            ("substitution", rate)
        )

    for rate in INSERTION_RATES:
        cases.append(
            ("insertion", rate)
        )

    for rate in DELETION_RATES:
        cases.append(
            ("deletion", rate)
        )

    for rate in MISSING_FRAGMENT_RATES:
        cases.append(
            ("missing_fragment", rate)
        )

    # --------------------------------------------------------
    # Run experiments
    # --------------------------------------------------------

    results = []

    for error_type, rate in cases:

        row = run_case(
            error_type=error_type,
            rate=rate,
            clean_fragments=clean_fragments,
            original=original,
            expected_fragments=expected_fragments,
        )

        results.append(row)

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "error_type",
        "requested_rate",
        "affected_fragments",
        "affected_bases",
        "deleted_fragments",
        "expected_fragments",
        "retrieved_fragments",
        "reconstructed_bytes",
        "original_bytes",
        "retrieval_complete",
        "exact_reconstruction",
        "decoding_error",
    ]

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(results)

    # --------------------------------------------------------
    # Print substitution table
    # --------------------------------------------------------

    print("SUBSTITUTION SWEEP")
    print("-" * 60)

    print(
        "Rate       Bases    Fragments   Exact"
    )

    for row in results:

        if row["error_type"] != "substitution":
            continue

        print(
            f"{row['requested_rate']:<10} "
            f"{row['affected_bases']:<8} "
            f"{row['affected_fragments']:<11} "
            f"{str(row['exact_reconstruction'])}"
        )

    # --------------------------------------------------------
    # Print insertion table
    # --------------------------------------------------------

    print("")
    print("INSERTION SWEEP")
    print("-" * 60)

    print(
        "Rate       Bases    Fragments   Exact"
    )

    for row in results:

        if row["error_type"] != "insertion":
            continue

        print(
            f"{row['requested_rate']:<10} "
            f"{row['affected_bases']:<8} "
            f"{row['affected_fragments']:<11} "
            f"{str(row['exact_reconstruction'])}"
        )

    # --------------------------------------------------------
    # Print deletion table
    # --------------------------------------------------------

    print("")
    print("DELETION SWEEP")
    print("-" * 60)

    print(
        "Rate       Bases    Fragments   Exact"
    )

    for row in results:

        if row["error_type"] != "deletion":
            continue

        print(
            f"{row['requested_rate']:<10} "
            f"{row['affected_bases']:<8} "
            f"{row['affected_fragments']:<11} "
            f"{str(row['exact_reconstruction'])}"
        )

    # --------------------------------------------------------
    # Print missing fragment table
    # --------------------------------------------------------

    print("")
    print("MISSING-FRAGMENT SWEEP")
    print("-" * 60)

    print(
        "Rate       Missing    Retrieved   Exact"
    )

    for row in results:

        if row["error_type"] != "missing_fragment":
            continue

        print(
            f"{row['requested_rate']:<10} "
            f"{row['deleted_fragments']:<10} "
            f"{row['retrieved_fragments']:<11} "
            f"{str(row['exact_reconstruction'])}"
        )

    # --------------------------------------------------------
    # Count successful / failed exact reconstructions
    # --------------------------------------------------------

    total_cases = len(results)

    successful_cases = sum(
        1
        for row in results
        if row["exact_reconstruction"]
    )

    failed_cases = (
        total_cases
        - successful_cases
    )

    print("")
    print("=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)

    print(
        f"Total experiments    : {total_cases}"
    )

    print(
        f"Exact reconstructions: "
        f"{successful_cases}"
    )

    print(
        f"Failed reconstructions: "
        f"{failed_cases}"
    )

    print(
        f"Results CSV          : {OUTPUT}"
    )

    print("")
    print("=" * 60)
    print("RESULT: PASS")
    print("Systematic error-rate sweep completed.")
    print("Results were saved for quantitative analysis.")
    print("No physical DNA error-rate claim is made.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
