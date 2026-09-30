from __future__ import annotations

from pathlib import Path
import hashlib
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.fragmentation.fragmenter import (
    fragment_file,
    reconstruct_fragments,
)

from app.storage.archive import MolecularArchive


FRAGMENT_SIZE = 256

FILE_001 = ROOT / "data" / "input" / "archive_file_001.txt"
FILE_002 = ROOT / "data" / "input" / "archive_file_002.txt"
FILE_003 = ROOT / "data" / "input" / "archive_file_003_duplicate.txt"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:

    print("")
    print("=" * 60)
    print("MILESTONE 3 VERIFICATION")
    print("=" * 60)
    print("")

    # --------------------------------------------------------
    # Create fragments for all three files
    # --------------------------------------------------------

    fragments_001 = fragment_file(
        FILE_001,
        file_id="FILE_001",
        fragment_size=FRAGMENT_SIZE,
    )

    fragments_002 = fragment_file(
        FILE_002,
        file_id="FILE_002",
        fragment_size=FRAGMENT_SIZE,
    )

    fragments_003 = fragment_file(
        FILE_003,
        file_id="FILE_003",
        fragment_size=FRAGMENT_SIZE,
    )

    print("SOURCE FILES")
    print("-" * 60)

    print(
        f"FILE_001 : {len(FILE_001.read_bytes())} bytes | "
        f"{len(fragments_001)} fragments"
    )

    print(
        f"FILE_002 : {len(FILE_002.read_bytes())} bytes | "
        f"{len(fragments_002)} fragments"
    )

    print(
        f"FILE_003 : {len(FILE_003.read_bytes())} bytes | "
        f"{len(fragments_003)} fragments"
    )

    # --------------------------------------------------------
    # Verify duplicate payload
    # --------------------------------------------------------

    original_001 = FILE_001.read_bytes()
    original_003 = FILE_003.read_bytes()

    duplicate_payload = original_001 == original_003

    print("")
    print(
        f"FILE_001 == FILE_003 payload : "
        f"{duplicate_payload}"
    )

    if not duplicate_payload:
        raise SystemExit(
            "FAIL: Duplicate payload condition was not created."
        )

    # --------------------------------------------------------
    # Create mixed archive
    # --------------------------------------------------------

    archive = MolecularArchive(seed=42)

    archive.add_fragments(fragments_001)
    archive.add_fragments(fragments_002)
    archive.add_fragments(fragments_003)

    archive.seal()

    print("")
    print("SIMULATED MOLECULAR ARCHIVE")
    print("-" * 60)
    print(f"Total fragments : {archive.total_fragments}")

    expected_total = (
        len(fragments_001)
        + len(fragments_002)
        + len(fragments_003)
    )

    if archive.total_fragments != expected_total:
        raise SystemExit(
            "FAIL: Archive fragment count is incorrect."
        )

    # --------------------------------------------------------
    # Inspect mixed archive identity distribution
    # --------------------------------------------------------

    archive_fragments = archive.all_fragments()

    distribution = {}

    for fragment in archive_fragments:
        distribution[fragment.file_id] = (
            distribution.get(fragment.file_id, 0) + 1
        )

    print("")
    print("ARCHIVE DISTRIBUTION")
    print("-" * 60)

    for file_id in sorted(distribution):
        print(
            f"{file_id}: "
            f"{distribution[file_id]} fragments"
        )

    # --------------------------------------------------------
    # Selective retrieval: FILE_002
    # --------------------------------------------------------

    requested_file = "FILE_002"

    retrieved = archive.retrieve_by_file_id(
        requested_file
    )

    print("")
    print("SELECTIVE RETRIEVAL")
    print("-" * 60)
    print(f"Requested file : {requested_file}")
    print(f"Retrieved      : {len(retrieved)} fragments")

    # Verify every returned fragment belongs to requested file
    correct_identity = all(
        fragment.file_id == requested_file
        for fragment in retrieved
    )

    print(
        f"Identity filter : {correct_identity}"
    )

    if not correct_identity:
        raise SystemExit(
            "FAIL: Retrieval returned a fragment from another file."
        )

    # --------------------------------------------------------
    # Reconstruct FILE_002
    # --------------------------------------------------------

    reconstructed_002 = reconstruct_fragments(
        retrieved
    )

    original_002 = FILE_002.read_bytes()

    reconstruction_success = (
        reconstructed_002 == original_002
    )

    print(
        f"Reconstruction  : {reconstruction_success}"
    )

    if not reconstruction_success:
        raise SystemExit(
            "FAIL: FILE_002 reconstruction failed."
        )

    # --------------------------------------------------------
    # Verify FILE_001 and FILE_003 remain distinguishable
    # despite identical payloads.
    # --------------------------------------------------------

    retrieved_001 = archive.retrieve_by_file_id(
        "FILE_001"
    )

    retrieved_003 = archive.retrieve_by_file_id(
        "FILE_003"
    )

    identity_separation = (
        all(f.file_id == "FILE_001" for f in retrieved_001)
        and
        all(f.file_id == "FILE_003" for f in retrieved_003)
        and
        retrieved_001
        and
        retrieved_003
    )

    print("")
    print("DUPLICATE PAYLOAD IDENTITY TEST")
    print("-" * 60)
    print(
        f"FILE_001 payload == FILE_003 payload : "
        f"{duplicate_payload}"
    )
    print(
        f"FILE_001 fragments retrieved         : "
        f"{len(retrieved_001)}"
    )
    print(
        f"FILE_003 fragments retrieved         : "
        f"{len(retrieved_003)}"
    )
    print(
        f"Logical identities remain separate  : "
        f"{bool(identity_separation)}"
    )

    if not identity_separation:
        raise SystemExit(
            "FAIL: Duplicate payloads were not separated by file identity."
        )

    # --------------------------------------------------------
    # Display hashes as evidence that payloads are identical
    # while identities differ.
    # --------------------------------------------------------

    print("")
    print("PAYLOAD HASH COMPARISON")
    print("-" * 60)
    print(f"FILE_001 SHA-256 : {sha256(original_001)}")
    print(f"FILE_003 SHA-256 : {sha256(original_003)}")

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("RESULT: PASS")
    print("Mixed archive contains multiple logical files.")
    print("Selective retrieval returns only the requested file.")
    print("Identical payloads remain distinguishable by File ID.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
