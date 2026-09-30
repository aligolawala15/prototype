from __future__ import annotations

from pathlib import Path

from app.models.fragment import Fragment


def fragment_bytes(
    data: bytes,
    file_id: str,
    fragment_size: int = 256,
) -> list[Fragment]:
    """
    Split bytes into ordered fragments.

    The final fragment may be smaller than fragment_size.
    """

    if not file_id:
        raise ValueError("file_id cannot be empty.")

    if fragment_size <= 0:
        raise ValueError("fragment_size must be greater than zero.")

    fragments: list[Fragment] = []

    for start in range(0, len(data), fragment_size):
        fragment_number = start // fragment_size

        payload = data[start:start + fragment_size]

        fragments.append(
            Fragment(
                file_id=file_id,
                fragment_id=fragment_number,
                payload=payload,
            )
        )

    return fragments


def fragment_file(
    input_path: str | Path,
    file_id: str,
    fragment_size: int = 256,
) -> list[Fragment]:
    """
    Read a file and split it into logical fragments.
    """

    data = Path(input_path).read_bytes()

    return fragment_bytes(
        data=data,
        file_id=file_id,
        fragment_size=fragment_size,
    )


def reconstruct_fragments(
    fragments: list[Fragment],
) -> bytes:
    """
    Reconstruct the original bytes from fragments.

    Fragments are ordered by fragment_id before concatenation.
    """

    if not fragments:
        return b""

    file_ids = {fragment.file_id for fragment in fragments}

    if len(file_ids) != 1:
        raise ValueError(
            "Cannot reconstruct fragments belonging to multiple files."
        )

    ordered = sorted(
        fragments,
        key=lambda fragment: fragment.fragment_id,
    )

    return b"".join(
        fragment.payload
        for fragment in ordered
    )
