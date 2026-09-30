from __future__ import annotations

from app.dna_archive.archive import DNAArchive, decode_dna_fragments


def baseline_retrieve(
    archive: DNAArchive,
    file_id: str,
) -> bytes:
    """
    Baseline retrieval:

    1. Select fragments by logical File ID.
    2. Decode DNA sequences.
    3. Reconstruct the digital file.

    No integrity verification or error correction is performed.
    """

    fragments = archive.retrieve_by_file_id(
        file_id
    )

    return decode_dna_fragments(fragments)
