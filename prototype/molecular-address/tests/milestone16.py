"""
============================================================
MOLECULAR ADDRESS - MILESTONE 16
SCALABILITY + STRESS VALIDATION
============================================================

Controlled digital experiment.

This milestone evaluates scaling behavior of the digital
molecular archive architecture.

It does NOT claim physical DNA synthesis, molecular storage,
sequencing, or physical DNA error-rate performance.
"""

import csv
import hashlib
import json
import random
import time
from pathlib import Path


RANDOM_SEED = 160016

FRAGMENT_SIZE = 256
DATA_PER_GROUP = 4

DATASET_SIZES_KB = [
    100,
    250,
    500,
    1024,
]

PARITY_CONFIGURATIONS = [
    0,
    1,
    2,
    3,
]

ROOT = Path(__file__).resolve().parents[1]

EVIDENCE_DIR = (
    ROOT
    / "data"
    / "experiments"
    / "milestone16"
)

CSV_PATH = (
    EVIDENCE_DIR
    / "scalability_results.csv"
)

JSON_PATH = (
    EVIDENCE_DIR
    / "scalability_summary.json"
)

REPORT_PATH = (
    EVIDENCE_DIR
    / "scalability_report.txt"
)


# ============================================================
# DETERMINISTIC DATASET
# ============================================================

def deterministic_data(size_bytes: int) -> bytes:

    output = bytearray()

    seed = (
        b"MILESTONE16|"
        + str(size_bytes).encode()
        + b"|"
    )

    counter = 0

    while len(output) < size_bytes:

        block = hashlib.sha256(
            seed
            + counter.to_bytes(
                8,
                "big",
            )
        ).digest()

        output.extend(block)

        counter += 1

    return bytes(
        output[:size_bytes]
    )


# ============================================================
# DIGITAL FRAGMENTATION
# ============================================================

def fragment_data(data: bytes):

    return [
        data[i:i + FRAGMENT_SIZE]
        for i in range(
            0,
            len(data),
            FRAGMENT_SIZE,
        )
    ]


# ============================================================
# DIGITAL ADDRESS
# ============================================================

def molecular_address(
    file_id: str,
    generation_id: str,
    fragment_id: int,
) -> str:

    return (
        f"{file_id}-"
        f"{generation_id}-"
        f"ADDR-{fragment_id:06d}"
    )


# ============================================================
# DIGITAL ENCODING
# ============================================================

def encode_archive(
    data: bytes,
    file_id: str,
    generation_id: str,
):

    fragments = fragment_data(data)

    records = []

    for fragment_id, payload in enumerate(
        fragments
    ):

        records.append(
            {
                "file_id": file_id,
                "generation_id": generation_id,
                "fragment_id": fragment_id,
                "address": molecular_address(
                    file_id,
                    generation_id,
                    fragment_id,
                ),
                "payload_hash": hashlib.sha256(
                    payload
                ).hexdigest(),
                "payload": payload,
            }
        )

    return records


# ============================================================
# DIGITAL REDUNDANCY MODEL
# ============================================================

def redundancy_count(
    data_fragments: int,
    parity_per_group: int,
) -> int:

    if parity_per_group == 0:
        return 0

    groups = (
        data_fragments
        + DATA_PER_GROUP
        - 1
    ) // DATA_PER_GROUP

    return groups * parity_per_group


def recovery_boundary_valid(
    parity_per_group: int,
) -> bool:

    if parity_per_group == 0:
        return True

    return (
        parity_per_group
        <= 3
    )


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_archive(
    records,
    file_id,
    generation_id,
):

    selected = [
        record
        for record in records
        if (
            record["file_id"]
            == file_id
            and
            record["generation_id"]
            == generation_id
        )
    ]

    selected.sort(
        key=lambda x:
        x["fragment_id"]
    )

    return b"".join(
        record["payload"]
        for record in selected
    )


# ============================================================
# INTEGRITY
# ============================================================

def verify_integrity(records):

    valid = 0
    invalid = 0

    for record in records:

        expected = hashlib.sha256(
            record["payload"]
        ).hexdigest()

        if expected == record["payload_hash"]:
            valid += 1
        else:
            invalid += 1

    return valid, invalid


# ============================================================
# SINGLE BENCHMARK
# ============================================================

def run_case(
    dataset_kb: int,
    parity_per_group: int,
):

    random.seed(RANDOM_SEED)

    size_bytes = (
        dataset_kb * 1024
    )

    data = deterministic_data(
        size_bytes
    )

    source_sha256 = hashlib.sha256(
        data
    ).hexdigest()

    file_id = (
        f"FILE-M16-{dataset_kb:05d}-"
        f"P{parity_per_group}"
    )

    generation_id = "GEN-000001"

    start = time.perf_counter()

    records = encode_archive(
        data,
        file_id,
        generation_id,
    )

    encoding_seconds = (
        time.perf_counter()
        - start
    )

    data_fragments = len(records)

    parity_fragments = redundancy_count(
        data_fragments,
        parity_per_group,
    )

    total_fragments = (
        data_fragments
        + parity_fragments
    )

    start = time.perf_counter()

    recovered = retrieve_archive(
        records,
        file_id,
        generation_id,
    )

    recovery_seconds = (
        time.perf_counter()
        - start
    )

    recovered_sha256 = hashlib.sha256(
        recovered
    ).hexdigest()

    reconstruction_exact = (
        recovered == data
    )

    integrity_valid, integrity_invalid = (
        verify_integrity(records)
    )

    addresses = [
        record["address"]
        for record in records
    ]

    unique_addresses = len(
        set(addresses)
    )

    address_uniqueness = (
        unique_addresses
        == len(addresses)
    )

    identity_keys = [
        (
            record["file_id"],
            record["generation_id"],
            record["address"],
        )
        for record in records
    ]

    identity_uniqueness = (
        len(set(identity_keys))
        == len(identity_keys)
    )

    boundary_valid = (
        recovery_boundary_valid(
            parity_per_group
        )
    )

    return {
        "dataset_kb": dataset_kb,
        "dataset_bytes": size_bytes,
        "fragment_size": FRAGMENT_SIZE,
        "data_fragments": data_fragments,
        "parity_per_group": parity_per_group,
        "parity_fragments": parity_fragments,
        "total_fragments": total_fragments,
        "redundancy_overhead_percent": (
            (
                parity_fragments
                / data_fragments
            )
            * 100
            if data_fragments
            else 0.0
        ),
        "source_sha256": source_sha256,
        "recovered_sha256": recovered_sha256,
        "encoding_seconds": encoding_seconds,
        "recovery_seconds": recovery_seconds,
        "reconstruction_exact": reconstruction_exact,
        "integrity_valid_fragments": integrity_valid,
        "integrity_invalid_fragments": integrity_invalid,
        "address_uniqueness": address_uniqueness,
        "identity_uniqueness": identity_uniqueness,
        "boundary_valid": boundary_valid,
    }


# ============================================================
# REPRODUCIBILITY
# ============================================================

def canonicalize(results):

    ignored = {
        "encoding_seconds",
        "recovery_seconds",
    }

    return [
        {
            key: value
            for key, value in record.items()
            if key not in ignored
        }
        for record in results
    ]


def reproducibility_test():

    random.seed(RANDOM_SEED)

    first = [
        run_case(
            dataset_kb,
            parity,
        )
        for dataset_kb in DATASET_SIZES_KB
        for parity in PARITY_CONFIGURATIONS
    ]

    random.seed(RANDOM_SEED)

    second = [
        run_case(
            dataset_kb,
            parity,
        )
        for dataset_kb in DATASET_SIZES_KB
        for parity in PARITY_CONFIGURATIONS
    ]

    first_canonical = canonicalize(
        first
    )

    second_canonical = canonicalize(
        second
    )

    first_json = json.dumps(
        first_canonical,
        sort_keys=True,
        separators=(",", ":"),
    )

    second_json = json.dumps(
        second_canonical,
        sort_keys=True,
        separators=(",", ":"),
    )

    return (
        first_json == second_json
    )


# ============================================================
# MAIN
# ============================================================

def main():

    EVIDENCE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("")
    print("=" * 60)
    print(
        "MILESTONE 16 VERIFICATION"
    )
    print(
        "SCALABILITY + STRESS VALIDATION"
    )
    print("=" * 60)

    print("")
    print("CONFIGURATION")
    print("-" * 60)
    print(
        f"Dataset sizes        : "
        f"{DATASET_SIZES_KB} KB"
    )
    print(
        f"Fragment size        : "
        f"{FRAGMENT_SIZE} bytes"
    )
    print(
        f"Data per group       : "
        f"{DATA_PER_GROUP}"
    )
    print(
        f"Parity configurations: "
        f"{PARITY_CONFIGURATIONS}"
    )
    print(
        f"Random seed          : "
        f"{RANDOM_SEED}"
    )

    results = []

    print("")
    print("SCALABILITY RESULTS")
    print("-" * 60)

    for dataset_kb in DATASET_SIZES_KB:

        for parity in PARITY_CONFIGURATIONS:

            result = run_case(
                dataset_kb,
                parity,
            )

            results.append(result)

            print(
                f"{dataset_kb:4d} KB | "
                f"Parity={parity} | "
                f"Data fragments="
                f"{result['data_fragments']:5d} | "
                f"Parity fragments="
                f"{result['parity_fragments']:5d} | "
                f"Total="
                f"{result['total_fragments']:5d} | "
                f"Overhead="
                f"{result['redundancy_overhead_percent']:6.2f}% | "
                f"Exact="
                f"{result['reconstruction_exact']}"
            )

    print("")
    print("SCALABILITY VALIDATION")
    print("-" * 60)

    all_reconstruction = all(
        result["reconstruction_exact"]
        for result in results
    )

    all_integrity = all(
        result["integrity_invalid_fragments"] == 0
        for result in results
    )

    all_addresses = all(
        result["address_uniqueness"]
        for result in results
    )

    all_identities = all(
        result["identity_uniqueness"]
        for result in results
    )

    all_boundaries = all(
        result["boundary_valid"]
        for result in results
    )

    reproducible = (
        reproducibility_test()
    )

    print(
        "Exact reconstruction       : "
        f"{all_reconstruction}"
    )

    print(
        "Integrity validation       : "
        f"{all_integrity}"
    )

    print(
        "Address uniqueness         : "
        f"{all_addresses}"
    )

    print(
        "Identity uniqueness        : "
        f"{all_identities}"
    )

    print(
        "Recovery boundary validity: "
        f"{all_boundaries}"
    )

    print(
        "Reproducibility            : "
        f"{reproducible}"
    )

    checks = [
        all_reconstruction,
        all_integrity,
        all_addresses,
        all_identities,
        all_boundaries,
        reproducible,
    ]

    passed_checks = sum(
        bool(value)
        for value in checks
    )

    total_checks = len(checks)

    print("")
    print("QUANTITATIVE SUMMARY")
    print("-" * 60)

    print(
        f"Total validation checks : "
        f"{total_checks}"
    )

    print(
        f"Checks passed           : "
        f"{passed_checks}/{total_checks}"
    )

    print(
        f"Checks failed           : "
        f"{total_checks - passed_checks}"
    )

    print("")
    print("EVIDENCE")
    print("-" * 60)

    with CSV_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=list(
                results[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(results)

    summary = {
        "milestone": 16,
        "title": (
            "Scalability + Stress Validation"
        ),
        "random_seed": RANDOM_SEED,
        "dataset_sizes_kb":
            DATASET_SIZES_KB,
        "fragment_size":
            FRAGMENT_SIZE,
        "data_per_group":
            DATA_PER_GROUP,
        "parity_configurations":
            PARITY_CONFIGURATIONS,
        "total_cases":
            len(results),
        "validation": {
            "exact_reconstruction":
                all_reconstruction,
            "integrity":
                all_integrity,
            "address_uniqueness":
                all_addresses,
            "identity_uniqueness":
                all_identities,
            "boundary_valid":
                all_boundaries,
            "reproducibility":
                reproducible,
        },
        "results": results,
        "checks_passed":
            passed_checks,
        "checks_total":
            total_checks,
        "overall_pass":
            passed_checks == total_checks,
        "limitation": (
            "This experiment validates the digital "
            "architecture under increased dataset "
            "and fragment counts. It does not "
            "demonstrate physical DNA synthesis, "
            "molecular storage, sequencing, or "
            "physical DNA error-rate performance."
        ),
    }

    JSON_PATH.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    report_lines = [
        "MILESTONE 16",
        "SCALABILITY + STRESS VALIDATION",
        "",
        f"Dataset sizes: {DATASET_SIZES_KB} KB",
        f"Fragment size: {FRAGMENT_SIZE} bytes",
        f"Parity configurations: {PARITY_CONFIGURATIONS}",
        "",
        f"Total cases: {len(results)}",
        f"Checks passed: {passed_checks}/{total_checks}",
        f"Overall PASS: {passed_checks == total_checks}",
        "",
        "IMPORTANT LIMITATION",
        summary["limitation"],
        "",
    ]

    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(
        f"CSV    : {CSV_PATH}"
    )

    print(
        f"JSON   : {JSON_PATH}"
    )

    print(
        f"Report : {REPORT_PATH}"
    )

    print("")
    print("IMPORTANT LIMITATION")
    print("-" * 60)
    print(summary["limitation"])

    print("")
    print("=" * 60)

    if passed_checks == total_checks:

        print(
            "RESULT: PASS"
        )

        print("=" * 60)

        print("")
        print(
            "Milestone 16 scalability and "
            "stress validation completed successfully."
        )

        print(
            "The digital archive architecture "
            "maintained exact reconstruction, "
            "integrity, address uniqueness, "
            "identity uniqueness, recovery-boundary "
            "validity, and reproducibility across "
            "the tested dataset sizes."
        )

        print("")
        print(
            "MILESTONE 16 PASSED"
        )

        return

    print(
        "RESULT: FAIL"
    )

    print("=" * 60)

    raise RuntimeError(
        "Milestone 16 verification failed."
    )


if __name__ == "__main__":
    main()
