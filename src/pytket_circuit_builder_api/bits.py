from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class Bit:
    """One bit of data."""

    _id: UUID = field(init=False, default_factory=UUID)


class BitRegister:
    """A register of bits."""

    def __init__(self, size: int) -> None:
        """Initialize with size."""
        self.size = size
        self.bits = [Bit() for _ in range(size)]

    def __get_item__(self, index: int) -> Bit:
        """Get a bit."""
        return self.bits[index]
