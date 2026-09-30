from __future__ import annotations

import random

from app.models.addressed_dna_fragment import (
    AddressedDNAFragment,
)


DNA_BASES = (
    "A",
    "C",
    "G",
    "T",
)


def corrupt_one_fragment(
    fragment: AddressedDNAFragment,
    seed: int = 42,
) -> AddressedDNAFragment:
    """
    Deliberately modify exactly one DNA base while keeping
    the original integrity hash unchanged.

    This simulates a corrupted stored/retrieved DNA sequence.
    """

    rng = random.Random(seed)

    sequence = list(
        fragment.dna_sequence
    )

    if not sequence:
        raise ValueError(
            "Cannot corrupt an empty DNA sequence."
        )

    index = rng.randrange(
        len(sequence)
    )

    current = sequence[index]

    alternatives = [
        base
        for base in DNA_BASES
        if base != current
    ]

    sequence[index] = rng.choice(
        alternatives
    )

    return AddressedDNAFragment(
        file_id=fragment.file_id,
        fragment_id=fragment.fragment_id,
        dna_sequence="".join(sequence),
        integrity_hash=fragment.integrity_hash,
    )
