from pytket import Circuit, Qubit
from pytket._tket.passes import DecomposeBoxes
from pytket._tket.unit_id import BitRegister, QubitRegister
from pytket_circuit_builder_api.angle import Angle
from pytket_circuit_builder_api.commands.commands import (
    CX,
    CircBox,
    CRz,
    QControlled,
    Rz,
    pytket_circbox,
    pytket_operator,
)
from pytket_circuit_builder_api.commands.conditional import (
    Conditional,
    PytketCondition,
    QasmCondition,
)


def test_simple_circuit() -> None:
    Q = QubitRegister("Q", 5)
    circuit = Circuit.from_operation_list(
        [
            CX(Q[0], Q[1]),
            CRz(Angle(0.3), Q[1], Q[2]),
            CRz(Angle("a"), Q[3], Q[0]),
            CX(Q[4], Qubit("anc", 1)),
            QControlled(
                command=Rz(Angle(0.4), Q[0]),
                control_qubits=[Q[i] for i in [2, 3, 4]],
                control_state=[True, True, False],
            ),
        ],
    )
    print("")
    for command in circuit.get_commands():
        print(command)


def test_circbox_circuit() -> None:
    Q = QubitRegister("Q", 5)
    inner_circuit = Circuit.from_operation_list(
        [
            CX(Q[0], Q[1]),
            CRz(Angle(0.3), Q[1], Q[2]),
            CRz(Angle("a"), Q[3], Q[0]),
            CX(Q[4], Qubit("anc", 1)),
            QControlled(
                command=Rz(Angle(0.4), Q[0]),
                control_qubits=[Q[i] for i in [2, 3, 4]],
                control_state=[True, True, False],
            ),
        ],
    )
    outer_circuit = Circuit.from_operation_list(
        [
            CX(Q[0], Q[4]),
            CircBox(inner_circuit),
            CX(Q[3], Q[4]),
        ],
    )
    print("")
    for command in outer_circuit.get_commands():
        print(command)

    print("Decomposed:")
    DecomposeBoxes().apply(outer_circuit)
    for command in outer_circuit.get_commands():
        print(command)


def test_parametrized_command() -> None:
    @pytket_operator
    def cccrz(targ: Qubit, c1: Qubit, c2: Qubit, c3: Qubit) -> QControlled:
        return QControlled(
            command=Rz(Angle("b"), targ),
            control_qubits=[c1, c2, c3],
        )

    Q = QubitRegister("Q", 4)
    circuit = Circuit()
    circuit.add_q_register(Q)

    circuit.extend(
        [
            cccrz(Q[0], Q[1], Q[2], Q[3]),
            cccrz(Q[1], Q[2], Q[3], Q[0]),
            cccrz(Q[2], Q[3], Q[0], Q[1]),
        ],
    )

    print("")
    for command in circuit.get_commands():
        print(command)


def test_parametrized_circbox() -> None:
    @pytket_operator
    def circ_op(t: Qubit, c1: Qubit, c2: Qubit) -> CircBox:
        circ = Circuit()
        circ.add_qubit(t)
        circ.add_qubit(c1)
        circ.add_qubit(c2)
        circ.extend(
            [
                QControlled(
                    command=Rz(Angle("b"), t),
                    control_qubits=[c1, c2],
                ),
                CRz(Angle("a"), c1, c2),
            ],
        )
        return CircBox(circ)

    @pytket_circbox
    def my_subcircuit(q0: Qubit, q1: Qubit, q2: Qubit) -> CircBox:
        yield CX(q0, q1)
        yield CX(q1, q2)
        yield CX(q0, q2)
        yield circ_op(q0, q1, q2)

    Q = QubitRegister("Q", 4)
    circuit = Circuit()
    circuit.add_q_register(Q)
    circuit.add_command(
        circ_op(Q[3], Q[2], Q[1]),
    )
    circuit.add_command(
        my_subcircuit(Q[0], Q[1], Q[3]),
    )

    print("")
    for command in circuit.get_commands():
        print(command)

    print("Decomposed:")
    DecomposeBoxes().apply(circuit)
    for command in circuit.get_commands():
        print(command)


def test_less_simple_circuit() -> None:
    circuit = Circuit()
    q = QubitRegister("q", 5)
    depth = 6
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
    circuit.add_command(CRz(Angle("a"), q[4], m[0]))

    print("")
    for command in circuit.get_commands():
        print(command)


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
                expression=C[0],
            ),
        ),
    )

    circuit.add_command(
        Conditional(CX(Q[3], Q[1]), PytketCondition(C[0] | C[1] ^ C[2] | C[3] & C[4])),
    )

    circuit.add_command(
        Conditional(
            command=CRz(Angle(0.3), Q[0], Q[1]),
            condition=QasmCondition(
                bits=[C[i] for i in range(C.size)],
                value=3,
            ),
        ),
    )
    print("")
    for command in circuit.get_commands():
        print(command)
