from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AddressedDNAFragment:
    """
    DNA fragment with logical addressing and integrity metadata.

    file_id:
        Logical identity of the source file.

    fragment_id:
        Position of the fragment within that file.

    dna_sequence:
        Simulated DNA representation.

    integrity_hash:
        SHA-256 fingerprint of the expected DNA sequence.

    This is a computational model only.
    It does not represent physical DNA synthesis or sequencing.
    """

    file_id: str
    fragment_id: int
    dna_sequence: str
    integrity_hash: str

    @property
    def address(self) -> str:
        return (
            f"{self.file_id}"
            f"-FRAG-"
            f"{self.fragment_id:06d}"
        )
