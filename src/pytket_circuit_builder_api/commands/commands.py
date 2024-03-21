from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Self, TypeVar

from pytket import Bit, Circuit, OpType, Qubit
from pytket._tket.circuit import CircBox as TketCircBox
from pytket._tket.circuit import Op, QControlBox

from pytket_circuit_builder_api.angle import Angle
from pytket_circuit_builder_api.commands.command_interface import (
    TketCompatibleCommand,
)

Oprnd = TypeVar("Oprnd", Qubit, Bit)


def _is_unique_list(list_to_check: list[Any]) -> bool:
    return len(list_to_check) == len(set(list_to_check))


def _raise_if_operands_missing_from_circuit(
    circuit: Circuit,
    operands: Sequence[Qubit | Bit],
) -> None:
    circuit_operands: list[Qubit | Bit] = circuit.qubits + circuit.bits
    missing_operands: list[Qubit | Bit] = []
    for operand in operands:
        if operand not in circuit_operands:
            missing_operands.append(operand)
    msg = f"Operands {missing_operands} are not contained in circuit"
    if missing_operands:
        raise Exception(msg)


def _sub(operand: Oprnd, subs: dict[Oprnd, Oprnd]) -> Oprnd:
    return subs.get(operand, operand)


@dataclass(frozen=True)
class CX(TketCompatibleCommand):
    target: Qubit
    control: Qubit

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        _raise_if_operands_missing_from_circuit(circuit, self.qubits())
        circuit.add_gate(self.tket_op_type(), [self.target, self.control])

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] = {},
        bit_subs: dict[Bit, Bit] = {},
    ) -> Self:
        return CX(_sub(self.target, qubit_subs), _sub(self.control, qubit_subs))

    def params(self) -> list[Angle]:
        return []

    def qubits(self) -> list[Qubit]:
        return [self.target, self.control]

    def bits(self) -> list[Bit]:
        return []

    def tket_op_type(self) -> OpType:
        return OpType.CX

    def to_tket_op(self) -> Op:
        return Op.create(self.tket_op_type())


@dataclass(frozen=True)
class Rz(TketCompatibleCommand):
    angle: Angle
    qubit: Qubit

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        _raise_if_operands_missing_from_circuit(circuit, self.qubits())
        circuit.add_gate(self.tket_op_type(), self.angle.expr, [self.qubit])

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] = {},
        bit_subs: dict[Bit, Bit] = {},
    ) -> Self:
        return Rz(self.angle, _sub(self.qubit, qubit_subs))

    def params(self) -> list[Angle]:
        return [self.angle]

    def qubits(self) -> list[Qubit]:
        return [self.qubit]

    def bits(self) -> list[Bit]:
        return []

    def tket_op_type(self) -> OpType:
        return OpType.Rz

    def to_tket_op(self) -> Op:
        return Op.create(self.tket_op_type(), self.angle.expr)


@dataclass
class CRz(TketCompatibleCommand):
    angle: Angle
    target: Qubit
    control: Qubit

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        _raise_if_operands_missing_from_circuit(circuit, self.qubits())
        circuit.add_gate(
            self.tket_op_type(),
            self.angle.expr,
            [self.target, self.control],
        )

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] = {},
        bit_subs: dict[Bit, Bit] = {},
    ) -> Self:
        return CRz(
            self.angle,
            _sub(self.target, qubit_subs),
            _sub(self.control, qubit_subs),
        )

    def params(self) -> list[Angle]:
        return [self.angle]

    def qubits(self) -> list[Qubit]:
        return [self.target, self.control]

    def bits(self) -> list[Bit]:
        return []

    def tket_op_type(self) -> OpType:
        return OpType.CRz

    def to_tket_op(self) -> Op:
        return Op.create(self.tket_op_type(), self.angle.expr)


@dataclass
class QControlled(TketCompatibleCommand):
    command: TketCompatibleCommand
    control_qubits: Sequence[Qubit]
    control_state: Sequence[bool] = field(default_factory=list)
    _box: QControlBox | None = field(init=False, default=None)

    def __post_init__(self):
        if not _is_unique_list(self.qubits()):
            raise Exception("Operands aren't unique")
        if self.control_state:
            if len(self.control_state) != len(self.control_qubits):
                raise Exception(
                    "Control state length must match number of  control qubits",
                )
        else:
            self._control_state = [True for _ in self.control_qubits]

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        _raise_if_operands_missing_from_circuit(circuit, self.qubits())

        if not self._box:
            self._box = QControlBox(
                self.command.to_tket_op(),
                n=len(self.control_qubits),
                control_state=self.control_state,
            )
        assert self._box is not None
        circuit.add_qcontrolbox(self._box, self.qubits())

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] = {},
        bit_subs: dict[Bit, Bit] = {},
    ) -> Self:
        new_command = self.command.sub(qubit_subs, bit_subs)
        new_controls = [
            qubit_subs.get(old_control, old_control)
            for old_control in self.control_qubits
        ]
        result = QControlled(new_command, new_controls)
        result._box = self._box
        return result

    def params(self) -> list[Angle]:
        return self.command.params()

    def qubits(self) -> list[Qubit]:
        qubits = list(self.control_qubits)
        qubits.extend(self.command.qubits())
        return qubits

    def bits(self) -> list[Bit]:
        return self.command.bits()

    def tket_op_type(self) -> OpType:
        return OpType.QControlBox

    def to_tket_op(self) -> Op:
        return Op.create(self.tket_op_type())


class CircBox(TketCompatibleCommand):
    def __init__(self, circuit: Circuit) -> None:
        reverse_qubit_map: dict[Qubit, Qubit] = {}
        qubit_counter = 0
        self._qubits: list[Qubit] = []
        for qubit in circuit.qubits:
            self._qubits.append(qubit)
            reverse_qubit_map[qubit] = Qubit(qubit_counter)
            qubit_counter += 1

        reverse_bit_map: dict[Bit, Bit] = {}
        bit_counter = 0
        self._bits: list[Bit] = []
        for bit in circuit.bits:
            self._bits.append(bit)
            reverse_bit_map[bit] = Bit(bit_counter)
            bit_counter += 1

        self._circuit = circuit.copy()
        # make self._circuit simple
        self._circuit.rename_units(reverse_qubit_map)
        self._circuit.rename_units(reverse_bit_map)

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        _raise_if_operands_missing_from_circuit(circuit, self.qubits() + self._bits)
        circuit.add_circbox(TketCircBox(self._circuit), self.qubits())

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] = {},
        bit_subs: dict[Bit, Bit] = {},
    ) -> Self:
        new_circuit_op = CircBox(Circuit())
        new_circuit_op._circuit = self._circuit
        new_circuit_op._qubits = [_sub(qubit, qubit_subs) for qubit in self._qubits]
        new_circuit_op._bits = [_sub(bit, bit_subs) for bit in self._bits]
        return new_circuit_op

    def params(self) -> list[Angle]:
        return []

    def qubits(self) -> list[Qubit]:
        return self._qubits

    def bits(self) -> list[Bit]:
        return self._bits

    def tket_op_type(self) -> OpType:
        return OpType.CircBox

    def to_tket_op(self) -> Op:
        return Op.create(self.tket_op_type())


class CommandTemplate:
    def __init__(
        self,
        template_command: TketCompatibleCommand,
        template_qubits: Sequence[Qubit],
        template_bits: Sequence[Bit] = [],
    ) -> None:
        if set(template_command.qubits()) != set(template_qubits):
            raise Exception(
                "Templated qubits and bits must match signature of provided command exactly",
            )
        if set(template_command.bits()) != set(template_bits):
            raise Exception(
                "Templated qubits and bits must match signature of provided command exactly",
            )
        self.template_qubits = template_qubits
        self.template_bits = template_bits
        self.template_command = template_command

    def apply_to(
        self,
        qubits: Sequence[Qubit],
        bits: Sequence[Bit] = [],
    ) -> TketCompatibleCommand:
        if len(qubits) != len(self.template_qubits):
            raise Exception(
                "Number of provided qubits must match number in the template",
            )
        if len(bits) != len(self.template_bits):
            raise Exception("Number of provided bits must match number in the template")
        qubit_sub_map = {self.template_qubits[i]: qubits[i] for i in range(len(qubits))}
        bit_sub_map = {self.template_bits[i]: bits[i] for i in range(len(bits))}
        return self.template_command.sub(qubit_sub_map, bit_sub_map)
