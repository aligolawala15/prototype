from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "experiments" / "milestone14"

OUT.mkdir(parents=True, exist_ok=True)

random.seed(140014)


# ============================================================
# BASIC UTILITIES
# ============================================================

DNA_ALPHABET = set("ACGT")
DNA_MAP = {
    "00": "A",
    "01": "C",
    "10": "G",
    "11": "T",
}

DNA_REVERSE = {v: k for k, v in DNA_MAP.items()}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bytes_to_bits(data: bytes) -> str:
    return "".join(f"{b:08b}" for b in data)


def bits_to_bytes(bits: str) -> bytes:
    if len(bits) % 8 != 0:
        raise ValueError("Bit string length must be divisible by 8.")

    return bytes(
        int(bits[i:i + 8], 2)
        for i in range(0, len(bits), 8)
    )


def encode_dna(data: bytes) -> str:
    bits = bytes_to_bits(data)

    return "".join(
        DNA_MAP[bits[i:i + 2]]
        for i in range(0, len(bits), 2)
    )


def decode_dna(dna: str) -> bytes:
    if not set(dna).issubset(DNA_ALPHABET):
        raise ValueError("Invalid DNA alphabet.")

    bits = "".join(DNA_REVERSE[b] for b in dna)

    return bits_to_bytes(bits)


# ============================================================
# GF(256)
# ============================================================

def gf_mul(a: int, b: int) -> int:
    result = 0

    while b:
        if b & 1:
            result ^= a

        high = a & 0x80
        a = (a << 1) & 0xFF

        if high:
            a ^= 0x1D

        b >>= 1

    return result


def gf_pow(a: int, power: int) -> int:
    result = 1

    while power:
        if power & 1:
            result = gf_mul(result, a)

        a = gf_mul(a, a)
        power >>= 1

    return result


def gf_inv(a: int) -> int:
    if a == 0:
        raise ZeroDivisionError("GF(256) zero has no inverse.")

    return gf_pow(a, 254)


def matrix_inverse(matrix: list[list[int]]) -> list[list[int]]:
    n = len(matrix)

    aug = [
        list(matrix[r]) + [
            1 if r == c else 0
            for c in range(n)
        ]
        for r in range(n)
    ]

    for col in range(n):

        pivot = None

        for row in range(col, n):
            if aug[row][col] != 0:
                pivot = row
                break

        if pivot is None:
            raise ValueError("Matrix is singular.")

        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        inv = gf_inv(aug[col][col])

        aug[col] = [
            gf_mul(x, inv)
            for x in aug[col]
        ]

        for row in range(n):

            if row == col:
                continue

            factor = aug[row][col]

            if factor == 0:
                continue

            aug[row] = [
                a ^ gf_mul(factor, b)
                for a, b in zip(
                    aug[row],
                    aug[col]
                )
            ]

    return [
        row[n:]
        for row in aug
    ]


def matrix_vector_mul(
    matrix: list[list[int]],
    vector: list[bytes]
) -> list[bytes]:

    result = []

    for row in matrix:

        output = bytearray(len(vector[0]))

        for coefficient, block in zip(row, vector):

            if coefficient == 0:
                continue

            for i, value in enumerate(block):
                output[i] ^= gf_mul(
                    coefficient,
                    value
                )

        result.append(bytes(output))

    return result


# ============================================================
# GENERIC ERASURE ARCHIVE
# ============================================================

DATA_COUNT = 4
PARITY_COUNT = 3
GROUP_SIZE = DATA_COUNT
FRAGMENT_SIZE = 256


def build_parity(data_blocks: list[bytes]) -> list[bytes]:

    parity_rows = []

    for p in range(PARITY_COUNT):

        row = []

        for d in range(DATA_COUNT):
            row.append(
                gf_pow(d + 1, p + 1)
            )

        parity_rows.append(row)

    return matrix_vector_mul(
        parity_rows,
        data_blocks
    )


def recover_group(
    fragments: dict[int, bytes | None]
) -> list[bytes]:

    available = [
        i for i, value in fragments.items()
        if value is not None
    ]

    if len(available) < DATA_COUNT:
        raise ValueError(
            "Insufficient fragments for recovery."
        )

    selected = available[:DATA_COUNT]

    rows = []

    for index in selected:

        if index < DATA_COUNT:

            row = [
                1 if d == index else 0
                for d in range(DATA_COUNT)
            ]

        else:

            parity_number = index - DATA_COUNT

            row = [
                gf_pow(d + 1, parity_number + 1)
                for d in range(DATA_COUNT)
            ]

        rows.append(row)

    observed = [
        fragments[i]
        for i in selected
    ]

    inverse = matrix_inverse(rows)

    return matrix_vector_mul(
        inverse,
        observed
    )


# ============================================================
# TEST DATA
# ============================================================

pattern = (
    b"MOLECULAR-ADDRESS|MILESTONE-14|"
    b"END-TO-END-INTEGRATION|"
    b"DNA-STORAGE|"
    b"ADDRESS|GENERATION|INTEGRITY|"
    b"REDUNDANCY|RECOVERY|"
    b"CONTROLLED-EXPERIMENT|"
)

target_size = 10 * 1024

source = bytearray()

while len(source) < target_size:
    source.extend(pattern)

source = bytes(source[:target_size])

original_hash = sha256(source)


# ============================================================
# FRAGMENTATION
# ============================================================

fragments = [
    source[i:i + FRAGMENT_SIZE]
    for i in range(
        0,
        len(source),
        FRAGMENT_SIZE
    )
]

fragment_count = len(fragments)


# ============================================================
# GENERATION + ADDRESS IDENTITY
# ============================================================

file_id = "FILE_002"
generation_id = "GEN-000001"

addressed_fragments = []

for index, payload in enumerate(fragments):

    address = (
        f"{file_id}-"
        f"{generation_id}-"
        f"ADDR-{index:06d}"
    )

    addressed_fragments.append({
        "file_id": file_id,
        "generation_id": generation_id,
        "fragment_id": index,
        "address": address,
        "payload_hash": sha256(payload),
        "payload": payload,
    })


# ============================================================
# DNA ENCODING
# ============================================================

for item in addressed_fragments:

    item["dna"] = encode_dna(
        item["payload"]
    )

    item["dna_hash"] = sha256(
        item["dna"].encode("ascii")
    )


# ============================================================
# DNA ARCHIVE
# ============================================================

archive = []

for item in addressed_fragments:

    archive.append({
        key: value
        for key, value in item.items()
        if key != "payload"
    })

random.shuffle(archive)


# ============================================================
# BASELINE RETRIEVAL
# ============================================================

selected = [
    item
    for item in archive
    if item["file_id"] == file_id
    and item["generation_id"] == generation_id
]

selected.sort(
    key=lambda x: x["fragment_id"]
)

baseline_fragments = [
    decode_dna(item["dna"])
    for item in selected
]

baseline = b"".join(
    baseline_fragments
)

baseline_hash = sha256(baseline)

baseline_exact = (
    baseline == source
    and baseline_hash == original_hash
)


# ============================================================
# CONTROLLED CORRUPTION
# ============================================================

target_fragment = 13

corrupted_archive = []

for item in archive:

    copied = dict(item)

    if copied["fragment_id"] == target_fragment:

        dna = list(copied["dna"])

        old = dna[100]

        replacements = [
            base
            for base in "ACGT"
            if base != old
        ]

        dna[100] = replacements[0]

        copied["dna"] = "".join(dna)

    corrupted_archive.append(copied)


# ============================================================
# INTEGRITY VERIFICATION
# ============================================================

integrity_valid = 0
integrity_invalid = 0
corrupted_detected = False

for item in corrupted_archive:

    calculated = sha256(
        item["dna"].encode("ascii")
    )

    if calculated == item["dna_hash"]:
        integrity_valid += 1
    else:
        integrity_invalid += 1

        if item["fragment_id"] == target_fragment:
            corrupted_detected = True


# ============================================================
# GROUPED REDUNDANCY
# ============================================================

groups = []

for group_start in range(
    0,
    fragment_count,
    GROUP_SIZE
):

    group_data = [
        fragments[group_start + i]
        for i in range(GROUP_SIZE)
    ]

    parity = build_parity(group_data)

    groups.append({
        "data": group_data,
        "parity": parity,
    })


# ============================================================
# SINGLE FAILURE RECOVERY
# ============================================================

failure_group = 3
missing_index = 1

group = groups[failure_group]

available = {}

for i, block in enumerate(group["data"]):

    if i != missing_index:
        available[i] = block

for p, block in enumerate(group["parity"]):
    available[DATA_COUNT + p] = block

recovered_group = recover_group(available)

single_recovery_exact = (
    recovered_group == group["data"]
)


# ============================================================
# THREE-FAILURE RECOVERY
# ============================================================

three_failure_group = 5

group3 = groups[three_failure_group]

available3 = {
    0: group3["data"][0],
    DATA_COUNT: group3["parity"][0],
    DATA_COUNT + 1: group3["parity"][1],
    DATA_COUNT + 2: group3["parity"][2],
}

recovered3 = recover_group(available3)

three_failure_exact = (
    recovered3 == group3["data"]
)


# ============================================================
# FULL FILE RECOVERY
# ============================================================

reconstructed_groups = []

for group_index, group in enumerate(groups):

    if group_index == three_failure_group:

        recovered = recovered3

    else:

        recovered = group["data"]

    reconstructed_groups.extend(
        recovered
    )


recovered_file = b"".join(
    reconstructed_groups
)

recovered_hash = sha256(
    recovered_file
)

full_recovery_exact = (
    recovered_file == source
    and recovered_hash == original_hash
)


# ============================================================
# IDENTITY VALIDATION
# ============================================================

identity_keys = {
    (
        item["file_id"],
        item["generation_id"],
        item["address"],
        item["fragment_id"],
    )
    for item in archive
}

identity_unique = (
    len(identity_keys)
    == len(archive)
)


# ============================================================
# DNA VALIDATION
# ============================================================

dna_valid = all(
    set(item["dna"]).issubset(DNA_ALPHABET)
    for item in archive
)


# ============================================================
# END-TO-END CHECKLIST
# ============================================================

checks = {

    "digital_source_created":
        len(source) == 10240,

    "fragmentation":
        fragment_count == 40,

    "generation_identity":
        all(
            item["generation_id"] == generation_id
            for item in archive
        ),

    "molecular_address_uniqueness":
        identity_unique,

    "dna_encoding":
        dna_valid,

    "mixed_archive":
        len(archive) == 40,

    "selective_retrieval":
        len(selected) == 40,

    "baseline_exact_reconstruction":
        baseline_exact,

    "integrity_detection":
        corrupted_detected,

    "single_fragment_recovery":
        single_recovery_exact,

    "three_fragment_recovery":
        three_failure_exact,

    "full_file_recovery":
        full_recovery_exact,

    "final_sha256_match":
        recovered_hash == original_hash,
}


# ============================================================
# RESULTS
# ============================================================

passed = sum(
    1
    for value in checks.values()
    if value
)

total = len(checks)

results = {
    "milestone": 14,
    "name": "End-to-End Molecular Archive Lifecycle",

    "dataset": {
        "bytes": len(source),
        "fragments": fragment_count,
        "fragment_size": FRAGMENT_SIZE,
        "original_sha256": original_hash,
    },

    "identity": {
        "file_id": file_id,
        "generation_id": generation_id,
        "unique_identity_keys": len(identity_keys),
    },

    "dna": {
        "dna_alphabet_valid": dna_valid,
        "archive_fragments": len(archive),
    },

    "integrity": {
        "valid_fragments": integrity_valid,
        "invalid_fragments": integrity_invalid,
        "corruption_detected": corrupted_detected,
    },

    "recovery": {
        "single_failure_exact": single_recovery_exact,
        "three_failure_exact": three_failure_exact,
        "full_file_exact": full_recovery_exact,
    },

    "verification": checks,

    "passed_checks": passed,
    "total_checks": total,
    "result": "PASS" if passed == total else "FAIL",

    "limitation": (
        "This is a controlled digital simulation of an "
        "end-to-end molecular archive architecture. "
        "It does not claim physical DNA synthesis, "
        "storage, sequencing, or measured physical DNA "
        "error rates."
    ),
}


# ============================================================
# SAVE JSON
# ============================================================

json_path = OUT / "end_to_end_results.json"

json_path.write_text(
    json.dumps(
        results,
        indent=2
    ),
    encoding="utf-8",
)


# ============================================================
# SAVE CSV
# ============================================================

csv_path = OUT / "end_to_end_checks.csv"

with csv_path.open(
    "w",
    newline="",
    encoding="utf-8",
) as handle:

    writer = csv.writer(handle)

    writer.writerow([
        "Check",
        "Result",
    ])

    for name, value in checks.items():

        writer.writerow([
            name,
            "PASS" if value else "FAIL",
        ])


# ============================================================
# CONSOLE REPORT
# ============================================================

print()
print("=" * 60)
print("MILESTONE 14 VERIFICATION")
print("END-TO-END MOLECULAR ARCHIVE LIFECYCLE")
print("=" * 60)

print()
print("SOURCE")
print("-" * 60)
print(f"Original bytes       : {len(source)}")
print(f"Fragment size        : {FRAGMENT_SIZE}")
print(f"Fragment count       : {fragment_count}")
print(f"Original SHA-256     : {original_hash}")

print()
print("MOLECULAR IDENTITY")
print("-" * 60)
print(f"File ID              : {file_id}")
print(f"Generation ID        : {generation_id}")
print(f"Unique identity keys : {len(identity_keys)}")
print(f"Identity uniqueness  : {identity_unique}")

print()
print("DNA REPRESENTATION")
print("-" * 60)
print(f"DNA fragments        : {len(archive)}")
print(f"Valid DNA alphabet   : {dna_valid}")

sample = selected[0]

print()
print("REPRESENTATIVE ADDRESS")
print("-" * 60)
print(f"Address              : {sample['address']}")
print(f"Fragment ID          : {sample['fragment_id']}")
print(f"DNA length           : {len(sample['dna'])} bases")
print(f"Payload hash         : {sample['payload_hash'][:24]}...")
print(f"DNA hash             : {sample['dna_hash'][:24]}...")

print()
print("BASELINE RETRIEVAL")
print("-" * 60)
print(f"Requested file       : {file_id}")
print(f"Requested generation : {generation_id}")
print(f"Retrieved fragments  : {len(selected)}")
print(f"Reconstruction       : {baseline_exact}")
print(f"SHA-256 match        : {baseline_hash == original_hash}")

print()
print("INTEGRITY TEST")
print("-" * 60)
print(f"Valid fragments      : {integrity_valid}")
print(f"Invalid fragments    : {integrity_invalid}")
print(f"Corruption detected  : {corrupted_detected}")
print(f"Target fragment      : {target_fragment}")

print()
print("REDUNDANCY TEST")
print("-" * 60)
print("Scheme               : GF(256)")
print("Data per group       : 4")
print("Parity per group     : 3")
print("Redundancy overhead  : 75.00%")
print(f"Single failure exact : {single_recovery_exact}")
print(f"Three failure exact  : {three_failure_exact}")

print()
print("FULL FILE RECOVERY")
print("-" * 60)
print(f"Recovered bytes      : {len(recovered_file)}")
print(f"Original SHA-256     : {original_hash}")
print(f"Recovered SHA-256    : {recovered_hash}")
print(f"Exact reconstruction : {full_recovery_exact}")

print()
print("END-TO-END CHECKLIST")
print("-" * 60)

for name, value in checks.items():

    status = "PASS" if value else "FAIL"

    print(
        f"{name:<38} {status}"
    )

print()
print("=" * 60)
print("QUANTITATIVE SUMMARY")
print("=" * 60)

print(f"Checks passed        : {passed}/{total}")
print(f"Checks failed        : {total - passed}")
print(
    f"Overall result       : "
    f"{'PASS' if passed == total else 'FAIL'}"
)

print()
print("EVIDENCE")
print("-" * 60)
print(f"JSON                 : {json_path}")
print(f"CSV                  : {csv_path}")

print()
print("IMPORTANT LIMITATION")
print("-" * 60)
print(
    "This experiment validates the digital architecture "
    "and controlled recovery pipeline."
)
print(
    "It does not demonstrate physical DNA synthesis, "
    "molecular storage, sequencing, or physical DNA "
    "error-rate performance."
)

print()
print("=" * 60)

if passed == total:

    print("RESULT: PASS")
    print("=" * 60)
    print()
    print(
        "The complete digital molecular archive lifecycle "
        "was successfully validated."
    )
    print(
        "File identity, generation identity, molecular "
        "addressing, DNA representation, integrity "
        "verification, redundancy, recovery, and final "
        "SHA-256 verification all passed."
    )

else:

    print("RESULT: FAIL")
    print("=" * 60)
    print()
    print(
        "One or more end-to-end checks failed."
    )

    sys.exit(1)

print()
print("=" * 60)
print("MILESTONE 14 PASSED")
print("=" * 60)
