from pytket import Circuit, Qubit
from pytket._tket.passes import DecomposeBoxes
from pytket._tket.unit_id import QubitRegister, BitRegister
from pytket_circuit_builder_api.angle import Angle
from pytket_circuit_builder_api.commands.commands import (
    CX,
    CircBox,
    CommandTemplate,
    CRz,
    QControlled,
    Rz, pytket_circbox, pytket_operator,
)
from pytket_circuit_builder_api.commands.conditional import Conditional, PytketCondition, QasmCondition


def test_simple_circuit() -> None:
    Q = QubitRegister("Q", 5)
    M = QubitRegister("M", 3)

    circuit = Circuit.from_operation_list(
        [
            CX(Q[0], Q[1]),
            CRz(Angle(0.3), Q[1], Q[2]),
            CRz(Angle("a"), Q[3], Q[0]),
            CX(Q[4], Qubit("anc", 1)),
            QControlled(
                command=Rz(Angle(0.4), Q[0]),
                control_qubits=[Q[i] for i in [2, 3, 4]],
            ),
        ],
    )

    for command in circuit.get_commands():
        print(command)

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

    @pytket_operator
    def rz_nw(qubit: Qubit) -> Rz:
        """my func"""
        return Rz(Angle(0.3), qubit)

    @pytket_operator
    def ccrz(t: Qubit, c1: Qubit, c2: Qubit) -> QControlled:
        """my func"""
        return QControlled(
            command=Rz(Angle("b"), t),
            control_qubits=[c1, c2]
        )

    @pytket_operator
    def circ_op(t: Qubit, c1: Qubit, c2: Qubit) -> CircBox:
        """my func"""
        circ = Circuit()
        circ.add_qubit(t)
        circ.add_qubit(c1)
        circ.add_qubit(c2)
        circ.extend([
            QControlled(
                command=Rz(Angle("b"), t),
                control_qubits=[c1, c2]
            ),
            CX(c1, c2),
            CX(t, c2)
        ])
        return CircBox(circ)

    circuit.add_command(rz_nw(Q[0]))
    circuit.add_command(rz_nw(qubit=Q[2]))
    circuit.add_command(ccrz(c2=Q[0], c1=Q[3], t=Q[2]))
    circuit.extend([ccrz(c2=Q[0], c1=Q[3], t=Q[2])])

    @pytket_circbox
    def my_sub(q1: Qubit, q2: Qubit, q3: Qubit) -> CircBox:
        yield CX(q1, q2)
        yield CX(q2, q3)

    new_circ = Circuit()
    N = QubitRegister("N", 12)
    new_circ.add_q_register(N)
    new_circ.extend(
        [
            my_sub(N[0], N[1], N[2]),
            sub_circuit.apply_to([N[i] for i in range(6)]),
            sub_circuit.apply_to([N[i] for i in range(6, 12)]),
        ],
    )

    new_circ2 = Circuit()
    P = QubitRegister("P", 3)
    new_circ2.add_q_register(P)
    new_circ2.extend(
        [
            my_sub(P[0], P[1], P[2]),
        ],
    )

    assert len(circuit.qubits) == 6
    for command in circuit.get_commands():
        print(command)

    for command in new_circ.get_commands():
        print(command)

    for command in new_circ2.get_commands():
        print(command)
    DecomposeBoxes().apply(new_circ2)
    for command in new_circ2.get_commands():
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
    circuit.add_command(Rz(Angle("a"), m[0]))
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
    circuit.add_command(CircBox(inner_circ))
    return circuit


def test_conditional_circuit() -> None:
    Q = QubitRegister("Q", 5)
    C = BitRegister("C", 5)
    circuit = Circuit()
    circuit.add_q_register(Q)
    circuit.add_c_register(C)
    circuit.add_command(
        Conditional(
            command=CRz(Angle(0.3), Q[0], Q[1]),
            condition=PytketCondition(
                expression=C[0]
            )
        )
    )

    circuit.add_command(
        Conditional(CX(Q[3], Q[1]), PytketCondition(C[0] | C[1] ^ C[2] | C[3] & C[4]))
    )

    circuit.add_command(
        Conditional(
            command=CRz(Angle(0.3), Q[0], Q[1]),
            condition=QasmCondition(
                bits=[C[i] for i in range(C.size)],
                value=3
            )
        )
    )
    print("")
    for command in circuit.get_commands():
        print(command)
    
    
    
