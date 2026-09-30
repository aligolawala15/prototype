from __future__ import annotations

import random

from app.encoding.dna import (
    bytes_to_dna,
    dna_to_bytes,
)

from app.fragmentation.fragmenter import (
    fragment_file,
)

from app.models.dna_fragment import DNAFragment


def encode_file_to_dna_fragments(
    input_path,
    file_id: str,
    fragment_size: int = 256,
) -> list[DNAFragment]:
    """
    Read a digital file, fragment it, and convert each fragment
    payload into a simulated DNA sequence.
    """

    fragments = fragment_file(
        input_path=input_path,
        file_id=file_id,
        fragment_size=fragment_size,
    )

    return [
        DNAFragment(
            file_id=fragment.file_id,
            fragment_id=fragment.fragment_id,
            dna_sequence=bytes_to_dna(fragment.payload),
        )
        for fragment in fragments
    ]


def decode_dna_fragments(
    fragments: list[DNAFragment],
) -> bytes:
    """
    Decode DNA fragments back into digital bytes.

    Fragments are sorted by logical fragment ID before
    reconstruction.
    """

    if not fragments:
        return b""

    file_ids = {fragment.file_id for fragment in fragments}

    if len(file_ids) != 1:
        raise ValueError(
            "Cannot decode fragments belonging to multiple files."
        )

    ordered = sorted(
        fragments,
        key=lambda fragment: fragment.fragment_id,
    )

    return b"".join(
        dna_to_bytes(fragment.dna_sequence)
        for fragment in ordered
    )


class DNAArchive:
    """
    Simulated archive containing DNA-encoded fragments.
    """

    def __init__(self, seed: int = 42) -> None:
        self._fragments: list[DNAFragment] = []
        self._seed = seed

    def add_fragments(
        self,
        fragments: list[DNAFragment],
    ) -> None:
        self._fragments.extend(fragments)

    def seal(self) -> None:
        """
        Randomize physical pool order.
        """
        random.Random(self._seed).shuffle(
            self._fragments
        )

    @property
    def total_fragments(self) -> int:
        return len(self._fragments)

    def all_fragments(self) -> list[DNAFragment]:
        return self._fragments.copy()

    def retrieve_by_file_id(
        self,
        file_id: str,
    ) -> list[DNAFragment]:
        """
        Select fragments using their logical file identity.
        """
        return [
            fragment
            for fragment in self._fragments
            if fragment.file_id == file_id
        ]
