from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


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


INPUT = ROOT / "data" / "input" / "archive_file_002.txt"

FILE_ID = "FILE_002"

FRAGMENT_SIZE = 256

# Deliberately modest first-stage rates.
# These are simulation parameters, not claims about
# real-world sequencing error rates.

SUBSTITUTION_RATE = 0.001
INSERTION_RATE = 0.001
DELETION_RATE = 0.001
MISSING_FRAGMENT_RATE = 0.10

SEED = 42


def print_result(
    label,
    report,
    result,
):
    print("")
    print(label)
    print("-" * 60)

    print(
        f"Requested rate       : "
        f"{report.requested_rate}"
    )

    print(
        f"Affected fragments   : "
        f"{report.affected_fragments}"
    )

    print(
        f"Affected bases       : "
        f"{report.affected_bases}"
    )

    print(
        f"Deleted fragments    : "
        f"{report.deleted_fragments}"
    )

    print(
        f"Retrieved fragments  : "
        f"{result.retrieved_fragments}/"
        f"{result.expected_fragments}"
    )

    print(
        f"Reconstructed bytes   : "
        f"{result.reconstructed_bytes}"
    )

    print(
        f"Reconstruction       : "
        f"{result.reconstruction_success}"
    )

    if result.decoding_error:
        print(
            f"Decoding error       : "
            f"{result.decoding_error}"
        )


def main() -> None:

    print("")
    print("=" * 60)
    print("MILESTONE 5 VERIFICATION")
    print("CONTROLLED DNA CORRUPTION")
    print("=" * 60)
    print("")

    original = INPUT.read_bytes()

    clean_fragments = encode_file_to_dna_fragments(
        INPUT,
        file_id=FILE_ID,
        fragment_size=FRAGMENT_SIZE,
    )

    expected_fragments = len(clean_fragments)

    print("BASELINE")
    print("-" * 60)

    print(
        f"Original bytes       : "
        f"{len(original)}"
    )

    print(
        f"DNA fragments        : "
        f"{expected_fragments}"
    )

    # --------------------------------------------------------
    # Clean baseline
    # --------------------------------------------------------

    clean_result = retrieve_and_measure(
        clean_fragments,
        FILE_ID,
        expected_fragments,
        original,
    )

    print(
        f"Clean reconstruction : "
        f"{clean_result.reconstruction_success}"
    )

    if not clean_result.reconstruction_success:
        raise SystemExit(
            "FAIL: Clean baseline no longer reconstructs."
        )

    # --------------------------------------------------------
    # Substitution
    # --------------------------------------------------------

    corrupted, report = substitute_bases(
        clean_fragments,
        error_rate=SUBSTITUTION_RATE,
        seed=SEED,
    )

    result = retrieve_and_measure(
        corrupted,
        FILE_ID,
        expected_fragments,
        original,
    )

    print_result(
        "SUBSTITUTION EXPERIMENT",
        report,
        result,
    )

    # --------------------------------------------------------
    # Insertion
    # --------------------------------------------------------

    corrupted, report = insert_bases(
        clean_fragments,
        error_rate=INSERTION_RATE,
        seed=SEED,
    )

    result = retrieve_and_measure(
        corrupted,
        FILE_ID,
        expected_fragments,
        original,
    )

    print_result(
        "INSERTION EXPERIMENT",
        report,
        result,
    )

    # --------------------------------------------------------
    # Deletion
    # --------------------------------------------------------

    corrupted, report = delete_bases(
        clean_fragments,
        error_rate=DELETION_RATE,
        seed=SEED,
    )

    result = retrieve_and_measure(
        corrupted,
        FILE_ID,
        expected_fragments,
        original,
    )

    print_result(
        "DELETION EXPERIMENT",
        report,
        result,
    )

    # --------------------------------------------------------
    # Missing fragments
    # --------------------------------------------------------

    corrupted, report = delete_fragments(
        clean_fragments,
        fraction=MISSING_FRAGMENT_RATE,
        seed=SEED,
    )

    result = retrieve_and_measure(
        corrupted,
        FILE_ID,
        expected_fragments,
        original,
    )

    print_result(
        "MISSING-FRAGMENT EXPERIMENT",
        report,
        result,
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("RESULT: PASS")
    print("Controlled DNA corruption was successfully simulated.")
    print("The experiment measured its impact on reconstruction.")
    print("No claim about physical DNA error rates is made here.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
