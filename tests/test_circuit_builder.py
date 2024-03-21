from pytket import Circuit, Qubit
from pytket._tket.unit_id import QubitRegister
from pytket_circuit_builder_api.angle import Angle
from pytket_circuit_builder_api.commands.commands import (
    CX,
    CircBox,
    CommandTemplate,
    CRz,
    QControlled,
    Rz,
)


def test_simple_circuit() -> None:
    Q = QubitRegister("Q", 5)
    M = QubitRegister("M", 3)

    multi_controlled_rz = CommandTemplate(
        template_qubits=[M[0], M[1], M[2]],
        template_command=QControlled(
            command=Rz(Angle(0.3), M[0]),
            control_qubits=[M[1], M[2]],
        ),
    )

    circuit = Circuit.from_operation_list(
        [
            CX(Q[0], Q[1]),
            CRz(Angle(0.3), Q[1], Q[2]),
            CRz(Angle("a"), Q[3], Q[0]),
            CX(Q[4], Qubit("anc", 1)),
            multi_controlled_rz.apply_to([Q[0], Q[1], Q[2]], []),
        ],
    )

    sub_circuit = CommandTemplate(
        template_qubits=[*list(Q), Qubit("anc", 1)],
        template_command=CircBox(circuit),
    )

    new_circ = Circuit()
    N = QubitRegister("N", 12)
    new_circ.add_q_register(N)
    new_circ.extend(
        [
            sub_circuit.apply_to([N[i] for i in range(6)]),
            sub_circuit.apply_to([N[i] for i in range(6, 12)]),
        ],
    )

    assert len(circuit.qubits) == 6
    for command in circuit.get_commands():
        print(command)

    for command in new_circ.get_commands():
        print(command)


def test_less_simple_circuit(q: QubitRegister, depth: int) -> Circuit:
    circuit = Circuit()
    width = q.size
    m = QubitRegister("m", 1)
    circuit.add_q_register(q)
    circuit.add_q_register(m)
    circuit.extend(
        [
            CX(q[n], q[n + 1])
            for current_layer in range(depth)
            for n in range(current_layer % 2, width - 1, 2)
        ],
    )
    circuit.extend(
        [
            CRz(Angle(0.3), q[n + 1], q[n])
            for current_layer in range(depth)
            for n in range(current_layer % 2, width - 1, 2)
        ],
    )
    circuit.addd(Rz(Angle("a"), m[0]))
    return circuit


def test_circception() -> Circuit:
    circuit = Circuit()
    q = QubitRegister("data", 17)
    circuit.add_q_register(q)
    inner_circ = test_less_simple_circuit(QubitRegister("data", 3), 3)
    for c in inner_circ:
        print(c)
    for qubit in inner_circ.qubits:
        if qubit not in circuit.qubits:
            circuit.add_qubit(qubit)
    circuit.addd(CircBox(inner_circ))
    return circuit
