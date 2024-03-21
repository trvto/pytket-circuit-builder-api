from typing import Protocol, Self

from pytket import Bit, Circuit, OpType, Qubit
from pytket._tket.circuit import Op

from pytket_circuit_builder_api.angle import Angle


class Command(Protocol):
    """Protocol for circuit commands."""

    def append_to_circuit(self, circuit: Circuit) -> None:
        """Append command to circuit."""
        ...

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] | None = None,
        bit_subs: dict[Bit, Bit] | None = None,
    ) -> Self:
        """Substitute operands withing command."""
        ...

    def qubits(self) -> list[Qubit]:
        """Return all qubits within command."""
        ...

    def bits(self) -> list[Bit]:
        """Return all bits within command."""
        ...

    def params(self) -> list[Angle]:
        """Return all parameters within command."""
        ...

    def tket_op_type(self) -> OpType:
        """Return tket op type of command."""
        ...

    def to_tket_op(self) -> Op:
        """Return tket op of command."""
        ...
