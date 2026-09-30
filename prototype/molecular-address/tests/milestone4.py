from __future__ import annotations

from pathlib import Path
import hashlib
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.dna_archive.archive import (
    DNAArchive,
    encode_file_to_dna_fragments,
)

from app.retrieval.baseline import (
    baseline_retrieve,
)


FRAGMENT_SIZE = 256

FILE_001 = ROOT / "data" / "input" / "archive_file_001.txt"
FILE_002 = ROOT / "data" / "input" / "archive_file_002.txt"
FILE_003 = ROOT / "data" / "input" / "archive_file_003_duplicate.txt"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_dna_sequence(sequence: str) -> bool:
    return (
        len(sequence) > 0
        and set(sequence).issubset({"A", "C", "G", "T"})
    )


def main() -> None:

    print("")
    print("=" * 60)
    print("MILESTONE 4 VERIFICATION")
    print("=" * 60)
    print("")

    # --------------------------------------------------------
    # Encode all three files into DNA fragments
    # --------------------------------------------------------

    dna_001 = encode_file_to_dna_fragments(
        FILE_001,
        file_id="FILE_001",
        fragment_size=FRAGMENT_SIZE,
    )

    dna_002 = encode_file_to_dna_fragments(
        FILE_002,
        file_id="FILE_002",
        fragment_size=FRAGMENT_SIZE,
    )

    dna_003 = encode_file_to_dna_fragments(
        FILE_003,
        file_id="FILE_003",
        fragment_size=FRAGMENT_SIZE,
    )

    print("DNA ENCODING")
    print("-" * 60)

    print(
        f"FILE_001 : {len(dna_001)} DNA fragments"
    )

    print(
        f"FILE_002 : {len(dna_002)} DNA fragments"
    )

    print(
        f"FILE_003 : {len(dna_003)} DNA fragments"
    )

    # --------------------------------------------------------
    # Verify DNA alphabet
    # --------------------------------------------------------

    all_fragments = dna_001 + dna_002 + dna_003

    valid_sequences = all(
        validate_dna_sequence(
            fragment.dna_sequence
        )
        for fragment in all_fragments
    )

    print(
        f"Valid DNA alphabet : {valid_sequences}"
    )

    if not valid_sequences:
        raise SystemExit(
            "FAIL: Invalid character found in DNA sequence."
        )

    # --------------------------------------------------------
    # Display representative DNA
    # --------------------------------------------------------

    sample = dna_002[0]

    print("")
    print("REPRESENTATIVE DNA FRAGMENT")
    print("-" * 60)
    print(f"Address    : {sample.address}")
    print(f"DNA length : {sample.dna_length}")
    print(
        f"DNA sample : "
        f"{sample.dna_sequence[:120]}..."
    )

    # --------------------------------------------------------
    # Build DNA archive
    # --------------------------------------------------------

    archive = DNAArchive(seed=42)

    archive.add_fragments(dna_001)
    archive.add_fragments(dna_002)
    archive.add_fragments(dna_003)

    archive.seal()

    expected_total = (
        len(dna_001)
        + len(dna_002)
        + len(dna_003)
    )

    print("")
    print("DNA ARCHIVE")
    print("-" * 60)
    print(
        f"Total DNA fragments : "
        f"{archive.total_fragments}"
    )

    if archive.total_fragments != expected_total:
        raise SystemExit(
            "FAIL: DNA archive fragment count incorrect."
        )

    # --------------------------------------------------------
    # Inspect shuffled archive
    # --------------------------------------------------------

    pooled = archive.all_fragments()

    print(
        f"Pool order sample  : "
        f"{[f.address for f in pooled[:8]]}"
    )

    # --------------------------------------------------------
    # Baseline selective retrieval
    # --------------------------------------------------------

    requested_file = "FILE_002"

    reconstructed = baseline_retrieve(
        archive,
        requested_file,
    )

    original = FILE_002.read_bytes()

    reconstruction_success = (
        reconstructed == original
    )

    print("")
    print("BASELINE DNA RETRIEVAL")
    print("-" * 60)
    print(f"Requested file : {requested_file}")
    print(
        f"Original size  : {len(original)} bytes"
    )
    print(
        f"Retrieved size : {len(reconstructed)} bytes"
    )
    print(
        f"Reconstruction : "
        f"{reconstruction_success}"
    )

    if not reconstruction_success:
        raise SystemExit(
            "FAIL: DNA retrieval reconstruction failed."
        )

    # --------------------------------------------------------
    # Verify cryptographic equality after reconstruction.
    # This is measurement only; it is not yet the proposed
    # integrity mechanism.
    # --------------------------------------------------------

    original_hash = sha256(original)
    reconstructed_hash = sha256(reconstructed)

    print("")
    print("POST-RECONSTRUCTION COMPARISON")
    print("-" * 60)
    print(
        f"Original SHA-256      : {original_hash}"
    )
    print(
        f"Reconstructed SHA-256 : {reconstructed_hash}"
    )
    print(
        f"Hashes identical      : "
        f"{original_hash == reconstructed_hash}"
    )

    # --------------------------------------------------------
    # Verify that the archive still distinguishes identical
    # payloads through logical identity.
    # --------------------------------------------------------

    retrieved_001 = archive.retrieve_by_file_id(
        "FILE_001"
    )

    retrieved_003 = archive.retrieve_by_file_id(
        "FILE_003"
    )

    payload_001 = FILE_001.read_bytes()
    payload_003 = FILE_003.read_bytes()

    duplicate_payload = (
        payload_001 == payload_003
    )

    identity_separation = (
        all(
            fragment.file_id == "FILE_001"
            for fragment in retrieved_001
        )
        and
        all(
            fragment.file_id == "FILE_003"
            for fragment in retrieved_003
        )
    )

    print("")
    print("IDENTITY SEPARATION")
    print("-" * 60)
    print(
        f"Identical payloads : "
        f"{duplicate_payload}"
    )
    print(
        f"FILE_001 retrieved : "
        f"{len(retrieved_001)} fragments"
    )
    print(
        f"FILE_003 retrieved : "
        f"{len(retrieved_003)} fragments"
    )
    print(
        f"Identity separated : "
        f"{identity_separation}"
    )

    if not identity_separation:
        raise SystemExit(
            "FAIL: DNA archive identity separation failed."
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("RESULT: PASS")
    print("Digital files were represented as simulated DNA.")
    print("DNA sequences were stored in a mixed archive pool.")
    print("Selective retrieval reconstructed FILE_002 exactly.")
    print("Identical payloads remained logically distinguishable.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
