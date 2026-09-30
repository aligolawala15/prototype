from __future__ import annotations

import random
from dataclasses import dataclass

from app.models.dna_fragment import DNAFragment


DNA_BASES = ("A", "C", "G", "T")


@dataclass(frozen=True)
class ErrorReport:
    """
    Records what was intentionally changed during simulation.
    """

    error_type: str
    requested_rate: float
    affected_fragments: int
    affected_bases: int
    deleted_fragments: int


def _random_different_base(
    current: str,
    rng: random.Random,
) -> str:
    """
    Return a random DNA base different from current.
    """

    choices = [
        base
        for base in DNA_BASES
        if base != current
    ]

    return rng.choice(choices)


def substitute_bases(
    fragments: list[DNAFragment],
    error_rate: float,
    seed: int = 42,
) -> tuple[list[DNAFragment], ErrorReport]:
    """
    Randomly substitute DNA bases.

    Each base independently has probability error_rate
    of being replaced with a different valid DNA base.
    """

    if not 0 <= error_rate <= 1:
        raise ValueError(
            "error_rate must be between 0 and 1."
        )

    rng = random.Random(seed)

    output: list[DNAFragment] = []

    affected_fragments = set()
    affected_bases = 0

    for fragment in fragments:

        sequence = list(fragment.dna_sequence)

        for index, base in enumerate(sequence):

            if rng.random() < error_rate:

                sequence[index] = _random_different_base(
                    base,
                    rng,
                )

                affected_bases += 1
                affected_fragments.add(
                    fragment.fragment_id
                )

        output.append(
            DNAFragment(
                file_id=fragment.file_id,
                fragment_id=fragment.fragment_id,
                dna_sequence="".join(sequence),
            )
        )

    report = ErrorReport(
        error_type="substitution",
        requested_rate=error_rate,
        affected_fragments=len(affected_fragments),
        affected_bases=affected_bases,
        deleted_fragments=0,
    )

    return output, report


def insert_bases(
    fragments: list[DNAFragment],
    error_rate: float,
    seed: int = 42,
) -> tuple[list[DNAFragment], ErrorReport]:
    """
    Randomly insert DNA bases.

    Insertions intentionally change sequence length and therefore
    represent a more disruptive error than substitution.
    """

    if not 0 <= error_rate <= 1:
        raise ValueError(
            "error_rate must be between 0 and 1."
        )

    rng = random.Random(seed)

    output: list[DNAFragment] = []

    affected_fragments = set()
    affected_bases = 0

    for fragment in fragments:

        sequence: list[str] = []

        for base in fragment.dna_sequence:

            sequence.append(base)

            if rng.random() < error_rate:

                sequence.append(
                    rng.choice(DNA_BASES)
                )

                affected_bases += 1
                affected_fragments.add(
                    fragment.fragment_id
                )

        output.append(
            DNAFragment(
                file_id=fragment.file_id,
                fragment_id=fragment.fragment_id,
                dna_sequence="".join(sequence),
            )
        )

    report = ErrorReport(
        error_type="insertion",
        requested_rate=error_rate,
        affected_fragments=len(affected_fragments),
        affected_bases=affected_bases,
        deleted_fragments=0,
    )

    return output, report


def delete_bases(
    fragments: list[DNAFragment],
    error_rate: float,
    seed: int = 42,
) -> tuple[list[DNAFragment], ErrorReport]:
    """
    Randomly delete DNA bases.

    This can cause a DNA sequence length that is not divisible
    by two, which may prevent exact byte reconstruction.
    """

    if not 0 <= error_rate <= 1:
        raise ValueError(
            "error_rate must be between 0 and 1."
        )

    rng = random.Random(seed)

    output: list[DNAFragment] = []

    affected_fragments = set()
    affected_bases = 0

    for fragment in fragments:

        sequence: list[str] = []

        for base in fragment.dna_sequence:

            if rng.random() < error_rate:

                affected_bases += 1
                affected_fragments.add(
                    fragment.fragment_id
                )

                continue

            sequence.append(base)

        output.append(
            DNAFragment(
                file_id=fragment.file_id,
                fragment_id=fragment.fragment_id,
                dna_sequence="".join(sequence),
            )
        )

    report = ErrorReport(
        error_type="deletion",
        requested_rate=error_rate,
        affected_fragments=len(affected_fragments),
        affected_bases=affected_bases,
        deleted_fragments=0,
    )

    return output, report


def delete_fragments(
    fragments: list[DNAFragment],
    fraction: float,
    seed: int = 42,
) -> tuple[list[DNAFragment], ErrorReport]:
    """
    Remove complete fragments from the archive.
    """

    if not 0 <= fraction <= 1:
        raise ValueError(
            "fraction must be between 0 and 1."
        )

    if not fragments:
        return (
            [],
            ErrorReport(
                error_type="missing_fragment",
                requested_rate=fraction,
                affected_fragments=0,
                affected_bases=0,
                deleted_fragments=0,
            ),
        )

    rng = random.Random(seed)

    keep: list[DNAFragment] = []
    removed: list[DNAFragment] = []

    for fragment in fragments:

        if rng.random() < fraction:
            removed.append(fragment)
        else:
            keep.append(fragment)

    report = ErrorReport(
        error_type="missing_fragment",
        requested_rate=fraction,
        affected_fragments=len(removed),
        affected_bases=0,
        deleted_fragments=len(removed),
    )

    return keep, report
