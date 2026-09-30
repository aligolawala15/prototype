from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DNAFragment:
    """
    A fragment represented as a simulated DNA sequence.

    file_id:
        Logical identity of the source file.

    fragment_id:
        Position of the fragment in the source file.

    dna_sequence:
        Simulated DNA representation of the fragment payload.

    This class represents a computational model only.
    It does not represent physically synthesized DNA.
    """

    file_id: str
    fragment_id: int
    dna_sequence: str

    @property
    def address(self) -> str:
        """
        Logical address for the fragment.
        """
        return f"{self.file_id}-FRAG-{self.fragment_id:06d}"

    @property
    def dna_length(self) -> int:
        return len(self.dna_sequence)
