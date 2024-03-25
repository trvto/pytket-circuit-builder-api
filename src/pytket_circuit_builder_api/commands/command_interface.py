from collections.abc import Iterable
from typing import Protocol, Self

from pytket import Bit, Circuit, OpType, Qubit
from pytket._tket.circuit import Op

from pytket_circuit_builder_api.angle import Angle


class Command(Protocol):
    """Protocol for circuit commands."""

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] = {},
        bit_subs: dict[Bit, Bit] = {},
    ) -> Self:
        """Substitute operands withing command."""
        ...


class TketCompatibleCommand(Command, Protocol):
    """Protocol for circuit commands."""

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        """Append command to circuit."""

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


def append_func(self: Circuit, command: TketCompatibleCommand) -> None:
    """Add operation to circuit, qubits must be present."""
    command.append_to_tket_circuit(self)


def extend_func(self: Circuit, command: Iterable[TketCompatibleCommand]) -> None:
    """Add operations to circuit, qubits must be present."""
    for operation in command:
        operation.append_to_tket_circuit(self)


def from_operation_list_func(commands: Iterable[TketCompatibleCommand]) -> Circuit:
    """Construct a circuit from a list of operations, add qubits as needed."""
    circuit = Circuit()
    for command in commands:
        for qubit in command.qubits():
            circuit.add_qubit(qubit, reject_dups=False)
        command.append_to_tket_circuit(circuit)
    return circuit


Circuit.add_command = append_func
Circuit.extend = extend_func
Circuit.from_operation_list = from_operation_list_func
