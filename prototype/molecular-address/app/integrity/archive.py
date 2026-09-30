from __future__ import annotations

import random

from app.models.dna_fragment import DNAFragment

from app.models.addressed_dna_fragment import (
    AddressedDNAFragment,
)

from app.integrity.verification import (
    address_fragment,
    verify_fragments,
)


class AddressedDNAArchive:
    """
    Simulated molecular archive containing addressed
    DNA fragments with integrity fingerprints.
    """

    def __init__(
        self,
        seed: int = 42,
    ) -> None:

        self._fragments: list[
            AddressedDNAFragment
        ] = []

        self._seed = seed

    def add_dna_fragments(
        self,
        fragments: list[DNAFragment],
    ) -> None:

        for fragment in fragments:

            self._fragments.append(
                address_fragment(fragment)
            )

    def add_addressed_fragments(
        self,
        fragments: list[AddressedDNAFragment],
    ) -> None:

        self._fragments.extend(fragments)

    def seal(self) -> None:

        random.Random(
            self._seed
        ).shuffle(
            self._fragments
        )

    @property
    def total_fragments(self) -> int:
        return len(self._fragments)

    def all_fragments(
        self,
    ) -> list[AddressedDNAFragment]:

        return self._fragments.copy()

    def retrieve_by_file_id(
        self,
        file_id: str,
    ) -> list[AddressedDNAFragment]:

        return [
            fragment
            for fragment in self._fragments
            if fragment.file_id == file_id
        ]

    def verify_file(
        self,
        file_id: str,
    ) -> tuple[
        list[AddressedDNAFragment],
        list[AddressedDNAFragment],
    ]:

        fragments = self.retrieve_by_file_id(
            file_id
        )

        return verify_fragments(
            fragments
        )
