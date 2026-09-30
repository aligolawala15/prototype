from __future__ import annotations

import hashlib

from app.models.dna_fragment import DNAFragment

from app.models.addressed_dna_fragment import (
    AddressedDNAFragment,
)


def calculate_dna_hash(
    dna_sequence: str,
) -> str:
    """
    Calculate SHA-256 over the DNA sequence.
    """

    return hashlib.sha256(
        dna_sequence.encode("ascii")
    ).hexdigest()


def address_fragment(
    fragment: DNAFragment,
) -> AddressedDNAFragment:
    """
    Attach a deterministic integrity fingerprint to a DNA fragment.
    """

    return AddressedDNAFragment(
        file_id=fragment.file_id,
        fragment_id=fragment.fragment_id,
        dna_sequence=fragment.dna_sequence,
        integrity_hash=calculate_dna_hash(
            fragment.dna_sequence
        ),
    )


def verify_fragment(
    fragment: AddressedDNAFragment,
) -> bool:
    """
    Recalculate the DNA fingerprint and compare it
    with the stored expected fingerprint.
    """

    calculated = calculate_dna_hash(
        fragment.dna_sequence
    )

    return calculated == fragment.integrity_hash


def verify_fragments(
    fragments: list[AddressedDNAFragment],
) -> tuple[
    list[AddressedDNAFragment],
    list[AddressedDNAFragment],
]:
    """
    Separate fragments into valid and corrupted groups.
    """

    valid = []
    invalid = []

    for fragment in fragments:

        if verify_fragment(fragment):
            valid.append(fragment)
        else:
            invalid.append(fragment)

    return valid, invalid
