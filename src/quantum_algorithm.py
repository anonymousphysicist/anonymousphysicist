# src/quantum_algorithm.py

from qiskit import QuantumCircuit, Aer, transpile, assemble

def create_quantum_circuit():
    # Create a simple quantum circuit with 2 qubits and 2 classical bits
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc

def run_quantum_algorithm():
    qc = create_quantum_circuit()
    simulator = Aer.get_backend('qasm_simulator')
    compiled_circuit = transpile(qc, simulator)
    qobj = assemble(compiled_circuit)
    result = simulator.run(qobj).result()
    counts = result.get_counts(qc)
    return counts
