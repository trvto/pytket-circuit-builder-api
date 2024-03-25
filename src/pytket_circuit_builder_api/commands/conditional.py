from dataclasses import dataclass
from typing import Protocol, Sequence, Union, Self

from pytket import Qubit, Circuit, Bit, OpType
from pytket._tket.circuit import Op
from pytket.circuit.logic_exp import PredicateExp, BitLogicExp

from pytket_circuit_builder_api.angle import Angle
from pytket_circuit_builder_api.commands.command_interface import TketCompatibleCommand
from pytket_circuit_builder_api.commands.commands import _raise_if_operands_missing_from_circuit, _sub


@dataclass(frozen=True)
class QasmCondition:
    bits: Sequence[Bit]
    value: int


@dataclass(frozen=True)
class PytketCondition:
    expression: Union[PredicateExp, Bit, BitLogicExp]


@dataclass(frozen=True)
class Conditional(TketCompatibleCommand):
    command: TketCompatibleCommand
    condition: Union[QasmCondition, PytketCondition]

    def append_to_tket_circuit(self, circuit: Circuit) -> None:
        _raise_if_operands_missing_from_circuit(circuit, self.qubits() + self.bits())
        if isinstance(self.condition, QasmCondition):
            circuit.add_gate(
                self.command.to_tket_op(),
                self.command.qubits(),
                condition_bits=self.condition.bits,
                condition_value=self.condition.value
            )
        elif isinstance(self.condition, PytketCondition):
            circuit.add_gate(
                self.command.to_tket_op(),
                self.command.qubits(),
                condition=self.condition.expression,
            )
        else:
            raise TypeError

    def sub(
        self,
        qubit_subs: dict[Qubit, Qubit] = {},
        bit_subs: dict[Bit, Bit] = {},
    ) -> Self:
        """To do (condition stuff makes it a bit annoying)"""
        raise NotImplemented

    def params(self) -> list[Angle]:
        return self.command.params()

    def qubits(self) -> list[Qubit]:
        return self.command.qubits()

    def bits(self) -> list[Bit]:
        return []

    def tket_op_type(self) -> OpType:
        return OpType.Conditional

    def to_tket_op(self) -> Op:
        return Op.create(self.tket_op_type())
