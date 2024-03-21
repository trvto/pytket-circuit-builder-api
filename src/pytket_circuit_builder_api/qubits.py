from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class Qubit:
    """One qubit of data."""

    _id: UUID = field(init=False, default_factory=UUID)


class QubitRegister:
    """A register of qubits."""

    def __init__(self, size: int) -> None:
        """Initialize with size."""
        self.size = size
        self.qubits = [Qubit() for _ in range(size)]

    def __get_item__(self, index: int) -> Qubit:
        """Return a qubit."""
        return self.qubits[index]
