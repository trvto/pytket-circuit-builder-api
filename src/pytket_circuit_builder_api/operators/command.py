from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from pytket import Circuit, Qubit
from pytket._tket.circuit import CircBox as TketCircBox

from pytket_circuit_builder_api.operators.operator_interface import (
    TketCompatibleOperator,
)


@dataclass
class OpCommand:
    operator: TketCompatibleOperator
    qubits: Sequence[Qubit]
    append_logic: str = "standard"

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        """Append command to circuit."""
        if self.append_logic == "circbox":
            circuit.add_circbox(TketCircBox(self.operator._circuit), self.qubits)
        elif self.append_logic == "qcontrol":
            circuit.add_qcontrolbox(self.operator._box, self.qubits)
        else:
            circuit.add_gate(self.operator.to_tket_op(), self.qubits)


def append_func2(self: Circuit, command: OpCommand) -> None:
    """Add operation to circuit, qubits must be present."""
    command.append_to_tket_circuit(self)


def extend_func2(self: Circuit, command: Iterable[OpCommand]) -> None:
    """Add operations to circuit, qubits must be present."""
    for operation in command:
        operation.append_to_tket_circuit(self)


def from_operation_list_func2(commands: Iterable[OpCommand]) -> Circuit:
    """Construct a circuit from a list of operations, add qubits as needed."""
    circuit = Circuit()
    for command in commands:
        for qubit in command.qubits:
            circuit.add_qubit(qubit, reject_dups=False)
        command.append_to_tket_circuit(circuit)
    return circuit


Circuit.add_command2 = append_func2
Circuit.extend2 = extend_func2
Circuit.from_operation_list2 = from_operation_list_func2
