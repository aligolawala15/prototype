from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fragment:
    """
    Represents one logical fragment of a digital file.

    file_id:
        Logical identity of the source file.

    fragment_id:
        Position of this fragment within the source file.

    payload:
        Original digital bytes belonging to this fragment.
    """

    file_id: str
    fragment_id: int
    payload: bytes

    @property
    def address(self) -> str:
        """
        Logical molecular address used by the simulation.

        This is an identity, not a physical storage location.
        """
        return f"{self.file_id}-FRAG-{self.fragment_id:06d}"

    @property
    def payload_size(self) -> int:
        return len(self.payload)
