from __future__ import annotations

from dataclasses import dataclass

from app.dna_archive.archive import (
    decode_dna_fragments,
)

from app.models.dna_fragment import DNAFragment


@dataclass(frozen=True)
class RetrievalResult:
    """
    Result of one retrieval experiment.
    """

    requested_file: str
    expected_fragments: int
    retrieved_fragments: int
    reconstructed_bytes: int
    reconstruction_success: bool
    decoding_error: str | None


def retrieve_and_measure(
    fragments: list[DNAFragment],
    requested_file: str,
    expected_fragments: int,
    original_bytes: bytes,
) -> RetrievalResult:
    """
    Attempt reconstruction and record whether exact recovery
    succeeded.
    """

    selected = [
        fragment
        for fragment in fragments
        if fragment.file_id == requested_file
    ]

    try:

        reconstructed = decode_dna_fragments(
            selected
        )

        success = (
            reconstructed == original_bytes
        )

        return RetrievalResult(
            requested_file=requested_file,
            expected_fragments=expected_fragments,
            retrieved_fragments=len(selected),
            reconstructed_bytes=len(reconstructed),
            reconstruction_success=success,
            decoding_error=None,
        )

    except Exception as exc:

        return RetrievalResult(
            requested_file=requested_file,
            expected_fragments=expected_fragments,
            retrieved_fragments=len(selected),
            reconstructed_bytes=0,
            reconstruction_success=False,
            decoding_error=f"{type(exc).__name__}: {exc}",
        )
