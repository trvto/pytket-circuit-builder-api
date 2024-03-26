from pytket import Circuit, Qubit
from pytket._tket.passes import DecomposeBoxes
from pytket._tket.unit_id import QubitRegister
from pytket_circuit_builder_api.angle import Angle
from pytket_circuit_builder_api.operators.operators import (
    CX,
    CircBox,
    CRz,
    QControlled,
    Rz,
)


def test_simple_circuit() -> None:
    Q = QubitRegister("Q", 5)
    circuit = Circuit.from_operation_list2(
        [
            CX()(Q[0], Q[1]),
            Rz(Angle(0.3))(Q[1]),
            CRz(Angle("a"))(Q[3], Q[0]),
            CX()(Q[4], Qubit("anc", 1)),
            QControlled(
                operator=Rz(Angle(0.4)),
                n_control_qubits=3,
                control_state=[True, True, False],
            )([Q[2], Q[3], Q[4], Q[0]]),
        ],
    )
    print("")
    for command in circuit.get_commands():
        print(command)


def test_circbox_circuit() -> None:
    Q = QubitRegister("Q", 5)
    inner_circuit = Circuit.from_operation_list2(
        [
            CX()(Q[0], Q[1]),
            CRz(Angle(0.3))(Q[1], Q[2]),
            CRz(Angle("a"))(Q[3], Q[0]),
            CX()(Q[4], Qubit("anc", 1)),
            QControlled(
                operator=Rz(Angle(0.4)),
                n_control_qubits=3,
                control_state=[True, True, False],
            )([Q[2], Q[3], Q[4], Q[0]]),
        ],
    )
    outer_circuit = Circuit.from_operation_list2(
        [
            CX()(Q[0], Q[4]),
            CircBox(inner_circuit)([Q[0], Q[1], Q[2], Q[3], Qubit("anc", 1), Q[4]]),
            CX()(Q[3], Q[4]),
        ],
    )
    print("")
    for command in outer_circuit.get_commands():
        print(command)

    print("Decomposed:")
    DecomposeBoxes().apply(outer_circuit)
    for command in outer_circuit.get_commands():
        print(command)
