from __future__ import annotations

import random

from app.models.fragment import Fragment


class MolecularArchive:
    """
    Simulated molecular archive.

    The archive stores fragments in an intentionally unordered pool.

    This is a computational abstraction. It does not represent
    physically synthesized DNA molecules.
    """

    def __init__(self, seed: int = 42) -> None:
        self._fragments: list[Fragment] = []
        self._seed = seed

    def add_fragments(
        self,
        fragments: list[Fragment],
    ) -> None:
        """
        Add fragments to the archive.
        """
        self._fragments.extend(fragments)

    def seal(self) -> None:
        """
        Shuffle the archive to remove input ordering.
        """
        rng = random.Random(self._seed)
        rng.shuffle(self._fragments)

    @property
    def total_fragments(self) -> int:
        return len(self._fragments)

    def all_fragments(self) -> list[Fragment]:
        """
        Return a copy of the archive pool.
        """
        return self._fragments.copy()

    def retrieve_by_file_id(
        self,
        file_id: str,
    ) -> list[Fragment]:
        """
        Retrieve fragments belonging to exactly one logical file.

        File identity is based on file_id, not payload content.
        """
        return [
            fragment
            for fragment in self._fragments
            if fragment.file_id == file_id
        ]
