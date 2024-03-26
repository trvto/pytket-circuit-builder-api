from typing import Protocol

from pytket import OpType
from pytket._tket.circuit import Op

from pytket_circuit_builder_api.angle import Angle


class Operator(Protocol):
    """Protocol for circuit commands."""


class TketCompatibleOperator(Operator, Protocol):
    """Protocol for circuit commands."""

    def params(self) -> list[Angle]:
        """Return all parameters within command."""
        ...

    def tket_op_type(self) -> OpType:
        """Return tket op type of command."""
        ...

    def to_tket_op(self) -> Op:
        """Return tket op of command."""
        ...
