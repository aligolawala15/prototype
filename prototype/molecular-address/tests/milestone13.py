from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path


# ============================================================
# MOLECULAR ADDRESS - MILESTONE 13
# ADDRESS REUSE + GENERATION IDENTITY
# ============================================================


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "data" / "experiments" / "milestone13"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

RESULT_CSV = RESULT_DIR / "address_reuse_results.csv"
RESULT_JSON = RESULT_DIR / "address_reuse_results.json"


@dataclass(frozen=True)
class MolecularIdentity:
    file_id: str
    generation: int
    address: str
    payload_hash: str

    @property
    def identity_key(self) -> str:
        return (
            f"{self.file_id}:"
            f"GEN-{self.generation:06d}:"
            f"{self.address}"
        )


@dataclass
class Molecule:
    identity: MolecularIdentity
    fragment_index: int
    sequence: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_payload(label: str, size: int = 1024) -> bytes:
    pattern = (
        f"{label}|MOLECULAR-ADDRESS|"
        "GENERATION-IDENTITY|CONTROLLED-EXPERIMENT|"
    ).encode("utf-8")

    output = bytearray()

    while len(output) < size:
        output.extend(pattern)

    return bytes(output[:size])


def make_dna_like_sequence(data: bytes) -> str:
    """
    Deterministic simulation-only DNA representation.
    This is not a physical DNA synthesis model.
    """
    alphabet = "ACGT"

    digest = hashlib.sha256(data).digest()

    sequence = []

    for byte in digest:
        sequence.append(alphabet[(byte >> 6) & 0x03])
        sequence.append(alphabet[(byte >> 4) & 0x03])
        sequence.append(alphabet[(byte >> 2) & 0x03])
        sequence.append(alphabet[byte & 0x03])

    return "".join(sequence)


def create_identity(
    file_id: str,
    generation: int,
    address: str,
    payload: bytes,
) -> MolecularIdentity:

    return MolecularIdentity(
        file_id=file_id,
        generation=generation,
        address=address,
        payload_hash=sha256_bytes(payload),
    )


def create_archive_entry(
    identity: MolecularIdentity,
    payload: bytes,
) -> Molecule:

    sequence = make_dna_like_sequence(payload)

    return Molecule(
        identity=identity,
        fragment_index=0,
        sequence=sequence,
    )


def find_by_address(
    archive: list[Molecule],
    address: str,
) -> list[Molecule]:

    return [
        molecule
        for molecule in archive
        if molecule.identity.address == address
    ]


def find_by_full_identity(
    archive: list[Molecule],
    file_id: str,
    generation: int,
    address: str,
) -> list[Molecule]:

    return [
        molecule
        for molecule in archive
        if (
            molecule.identity.file_id == file_id
            and molecule.identity.generation == generation
            and molecule.identity.address == address
        )
    ]


def main() -> None:

    print()
    print("=" * 60)
    print("MILESTONE 13 VERIFICATION")
    print("ADDRESS REUSE + GENERATION IDENTITY")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # CONTROLLED PAYLOADS
    # --------------------------------------------------------

    payload_a = make_payload("FILE_A_GENERATION_1")
    payload_a1 = make_payload("FILE_A_GENERATION_2")

    payload_duplicate = payload_a

    hash_a = sha256_bytes(payload_a)
    hash_a1 = sha256_bytes(payload_a1)

    reused_address = "ADDR-000001"

    # --------------------------------------------------------
    # GENERATION 1
    # --------------------------------------------------------

    identity_a = create_identity(
        file_id="FILE_A",
        generation=1,
        address=reused_address,
        payload=payload_a,
    )

    molecule_a = create_archive_entry(
        identity_a,
        payload_a,
    )

    # --------------------------------------------------------
    # GENERATION 2
    #
    # Same logical file namespace.
    # Same molecular address.
    # New generation.
    # --------------------------------------------------------

    identity_a1 = create_identity(
        file_id="FILE_A",
        generation=2,
        address=reused_address,
        payload=payload_a1,
    )

    molecule_a1 = create_archive_entry(
        identity_a1,
        payload_a1,
    )

    # --------------------------------------------------------
    # IDENTICAL PAYLOAD REUSE TEST
    #
    # Generation 3 deliberately uses the exact same payload
    # as Generation 1 while reusing the same address.
    # --------------------------------------------------------

    identity_a_duplicate = create_identity(
        file_id="FILE_A",
        generation=3,
        address=reused_address,
        payload=payload_duplicate,
    )

    molecule_a_duplicate = create_archive_entry(
        identity_a_duplicate,
        payload_duplicate,
    )

    archive = [
        molecule_a,
        molecule_a1,
        molecule_a_duplicate,
    ]

    print("=" * 60)
    print("SOURCE IDENTITIES")
    print("-" * 60)

    for molecule in archive:
        identity = molecule.identity

        print(
            f"{identity.identity_key}"
            f" | HASH={identity.payload_hash[:16]}..."
        )

    print()

    # --------------------------------------------------------
    # TEST 1
    # ADDRESS REUSE
    # --------------------------------------------------------

    address_matches = find_by_address(
        archive,
        reused_address,
    )

    address_reuse_detected = len(address_matches) == 3

    print("=" * 60)
    print("T1 - ADDRESS REUSE")
    print("-" * 60)

    print(f"Reused address       : {reused_address}")
    print(f"Archive entries      : {len(address_matches)}")
    print(
        f"Address reuse detected: "
        f"{address_reuse_detected}"
    )

    # --------------------------------------------------------
    # TEST 2
    # ADDRESS-ONLY LOOKUP IS AMBIGUOUS
    # --------------------------------------------------------

    address_only_ambiguous = len(address_matches) > 1

    print()
    print("=" * 60)
    print("T2 - ADDRESS-ONLY LOOKUP")
    print("-" * 60)

    print(
        f"Entries sharing address : "
        f"{len(address_matches)}"
    )

    print(
        f"Address-only lookup ambiguous: "
        f"{address_only_ambiguous}"
    )

    # --------------------------------------------------------
    # TEST 3
    # GENERATION SEPARATION
    # --------------------------------------------------------

    generation_1_matches = find_by_full_identity(
        archive,
        "FILE_A",
        1,
        reused_address,
    )

    generation_2_matches = find_by_full_identity(
        archive,
        "FILE_A",
        2,
        reused_address,
    )

    generation_3_matches = find_by_full_identity(
        archive,
        "FILE_A",
        3,
        reused_address,
    )

    generation_separated = (
        len(generation_1_matches) == 1
        and len(generation_2_matches) == 1
        and len(generation_3_matches) == 1
    )

    print()
    print("=" * 60)
    print("T3 - GENERATION SEPARATION")
    print("-" * 60)

    print(
        f"Generation 1 matches : "
        f"{len(generation_1_matches)}"
    )

    print(
        f"Generation 2 matches : "
        f"{len(generation_2_matches)}"
    )

    print(
        f"Generation 3 matches : "
        f"{len(generation_3_matches)}"
    )

    print(
        f"Generation separation: "
        f"{generation_separated}"
    )

    # --------------------------------------------------------
    # TEST 4
    # SAME ADDRESS + SAME PAYLOAD
    # DIFFERENT GENERATION
    # --------------------------------------------------------

    same_payload = (
        identity_a.payload_hash
        == identity_a_duplicate.payload_hash
    )

    same_address = (
        identity_a.address
        == identity_a_duplicate.address
    )

    different_generation = (
        identity_a.generation
        != identity_a_duplicate.generation
    )

    logical_identity_separated = (
        same_payload
        and same_address
        and different_generation
        and (
            identity_a.identity_key
            != identity_a_duplicate.identity_key
        )
    )

    print()
    print("=" * 60)
    print("T4 - IDENTICAL PAYLOAD + REUSED ADDRESS")
    print("-" * 60)

    print(f"Same payload hash     : {same_payload}")
    print(f"Same molecular address: {same_address}")
    print(
        f"Different generation : "
        f"{different_generation}"
    )

    print(
        f"Logical identities separated: "
        f"{logical_identity_separated}"
    )

    # --------------------------------------------------------
    # TEST 5
    # FULL IDENTITY UNIQUENESS
    # --------------------------------------------------------

    identity_keys = [
        molecule.identity.identity_key
        for molecule in archive
    ]

    unique_identity_keys = (
        len(identity_keys)
        == len(set(identity_keys))
    )

    print()
    print("=" * 60)
    print("T5 - FULL MOLECULAR IDENTITY UNIQUENESS")
    print("-" * 60)

    print(
        f"Total identity keys : "
        f"{len(identity_keys)}"
    )

    print(
        f"Unique identity keys: "
        f"{len(set(identity_keys))}"
    )

    print(
        f"Identity uniqueness : "
        f"{unique_identity_keys}"
    )

    # --------------------------------------------------------
    # TEST 6
    # SELECTIVE RETRIEVAL BY GENERATION
    # --------------------------------------------------------

    requested_generation = 2

    selected = find_by_full_identity(
        archive,
        "FILE_A",
        requested_generation,
        reused_address,
    )

    selective_generation_retrieval = (
        len(selected) == 1
        and selected[0].identity.generation == 2
    )

    print()
    print("=" * 60)
    print("T6 - SELECTIVE GENERATION RETRIEVAL")
    print("-" * 60)

    print(
        f"Requested file      : FILE_A"
    )

    print(
        f"Requested generation: "
        f"GEN-{requested_generation:06d}"
    )

    print(
        f"Retrieved entries   : "
        f"{len(selected)}"
    )

    print(
        f"Correct generation  : "
        f"{selective_generation_retrieval}"
    )

    # --------------------------------------------------------
    # TEST 7
    # VERSIONED ADDRESS RECORD
    # --------------------------------------------------------

    address_records = []

    for molecule in archive:
        identity = molecule.identity

        address_records.append(
            {
                "file_id": identity.file_id,
                "generation": identity.generation,
                "address": identity.address,
                "payload_hash": identity.payload_hash,
                "identity_key": identity.identity_key,
            }
        )

    versioned_record_complete = all(
        record["file_id"]
        and record["generation"] >= 1
        and record["address"]
        and record["payload_hash"]
        and record["identity_key"]
        for record in address_records
    )

    print()
    print("=" * 60)
    print("T7 - VERSIONED ADDRESS RECORD")
    print("-" * 60)

    print(
        f"Complete identity metadata: "
        f"{versioned_record_complete}"
    )

    # --------------------------------------------------------
    # TEST 8
    # ADDRESS REUSE SAFETY RULE
    #
    # The system must not select an archive object using
    # address alone when multiple generations exist.
    # --------------------------------------------------------

    safe_retrieval_required = (
        address_only_ambiguous
        and generation_separated
    )

    print()
    print("=" * 60)
    print("T8 - ADDRESS REUSE SAFETY RULE")
    print("-" * 60)

    print(
        "Address alone sufficient : "
        f"{not address_only_ambiguous}"
    )

    print(
        "Generation required      : "
        f"{safe_retrieval_required}"
    )

    # --------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------

    tests = {
        "address_reuse_detected": address_reuse_detected,
        "address_only_is_ambiguous": address_only_ambiguous,
        "generation_separation": generation_separated,
        "identical_payload_identity_separation":
            logical_identity_separated,
        "full_identity_uniqueness": unique_identity_keys,
        "selective_generation_retrieval":
            selective_generation_retrieval,
        "versioned_record_complete":
            versioned_record_complete,
        "address_reuse_requires_generation":
            safe_retrieval_required,
    }

    passed = sum(1 for value in tests.values() if value)
    total = len(tests)

    # --------------------------------------------------------
    # SAVE CSV
    # --------------------------------------------------------

    csv_lines = [
        "test,result"
    ]

    for name, result in tests.items():
        csv_lines.append(
            f"{name},{str(result).lower()}"
        )

    RESULT_CSV.write_text(
        "\n".join(csv_lines) + "\n",
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    result_json = {
        "milestone": 13,
        "title": "Address Reuse + Generation Identity",
        "reused_address": reused_address,
        "archive_entries": len(archive),
        "address_only_matches": len(address_matches),
        "tests_total": total,
        "tests_passed": passed,
        "tests": tests,
        "identities": address_records,
        "limitation": (
            "This milestone validates logical identity and "
            "address reuse in a digital simulation. "
            "It does not establish physical DNA molecule "
            "identity, synthesis stability, or sequencing "
            "behavior."
        ),
    }

    RESULT_JSON.write_text(
        json.dumps(
            result_json,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print()
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
        f"Address reuse entries  : "
        f"{len(address_matches)}"
    )

    print(
        f"Unique full identities : "
        f"{len(set(identity_keys))}"
    )

    print()
    print("=" * 60)
    print("RESULT DATA")
    print("-" * 60)

    print(
        f"CSV saved to : "
        f"{RESULT_CSV}"
    )

    print(
        f"JSON saved to: "
        f"{RESULT_JSON}"
    )

    print()
    print("=" * 60)
    print("INTERPRETATION")
    print("-" * 60)

    print(
        "A molecular address can be reused across "
        "different logical generations."
    )

    print(
        "Therefore address alone is not sufficient "
        "to identify an archive object when reuse "
        "is permitted."
    )

    print(
        "Generation identity separates successive "
        "uses of the same address."
    )

    print(
        "The same payload and same address can still "
        "represent distinct logical archive generations."
    )

    print()
    print(
        "This is a controlled digital simulation."
    )

    print(
        "It does not claim physical DNA molecule "
        "identity or physical DNA storage behavior."
    )

    print()

    if passed != total:
        print("=" * 60)
        print("RESULT: FAIL")
        print("=" * 60)
        raise SystemExit(1)

    print("=" * 60)
    print("RESULT: PASS")
    print("=" * 60)

    print()
    print(
        "Address reuse was successfully demonstrated."
    )

    print(
        "Generation identity successfully separated "
        "reused molecular addresses."
    )

    print(
        "Identical payload + identical address + "
        "different generation remained distinguishable."
    )

    print()
    print("=" * 60)
    print("MILESTONE 13 PASSED")
    print("=" * 60)
    print()
    print("Terminal remains open. No termination command used.")
    print()


if __name__ == "__main__":
    main()
