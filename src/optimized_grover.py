import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator, noise
from qiskit.ignis.mitigation import complete_meas_cal, CompleteMeasFitter
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import time

def optimized_oracle(n, target_state):
    oracle = QuantumCircuit(n)
    for i, bit in enumerate(target_state):
        if bit == '0':
            oracle.x(i)
    oracle.mcx(list(range(n - 1)), n - 1)  # Multi-controlled Toffoli
    for i, bit in enumerate(target_state):
        if bit == '0':
            oracle.x(i)
    return oracle

def optimized_diffuser(n):
    diffuser = QuantumCircuit(n)
    diffuser.h(range(n))
    diffuser.x(range(n))
    diffuser.mcx(list(range(n - 1)), n - 1)  # Multi-controlled Toffoli
    diffuser.x(range(n))
    diffuser.h(range(n))
    return diffuser

def grover_circuit(n, target_state, num_iterations):
    circuit = QuantumCircuit(n)
    circuit.h(range(n))
    
    oracle = optimized_oracle(n, target_state)
    diffuser = optimized_diffuser(n)
    
    for _ in range(num_iterations):
        circuit.append(oracle, range(n))
        circuit.append(diffuser, range(n))
    
    circuit.measure_all()
    return circuit

def run_grover_test(n, target_state, num_iterations, shots=8192):
    simulator = AerSimulator()
    
    # Create a noise model
    noise_model = noise.NoiseModel()
    p_error = 0.01  # Error probability
    error = noise.depolarizing_error(p_error, 1)
    noise_model.add_all_qubit_quantum_error(error, 'u1')
    noise_model.add_all_qubit_quantum_error(error, 'u2')
    noise_model.add_all_qubit_quantum_error(error, 'u3')
    
    # Measurement error mitigation
    meas_calibs, state_labels = complete_meas_cal(qubit_list=range(n), circlabel='mcal')
    t_cals = transpile(meas_calibs, simulator)
    qobj_cals = simulator.run(t_cals, noise_model=noise_model, shots=shots)
    cal_results = qobj_cals.result()
    meas_fitter = CompleteMeasFitter(cal_results, state_labels, circlabel='mcal')

    circuit = grover_circuit(n, target_state, num_iterations)
    compiled_circuit = transpile(circuit, simulator, optimization_level=3)
    
    start_time = time.time()
    result = simulator.run(compiled_circuit, shots=shots, noise_model=noise_model).result()
    execution_time = time.time() - start_time
    
    counts = result.get_counts()
    mitigated_counts = meas_fitter.filter.apply(counts)
    
    return mitigated_counts, execution_time

def optimize_etpt_algorithm():
    num_qubits_list = [2, 3, 4, 5]
    num_iterations_list = [1, 2, 3]
    shots = 8192
    best_config = None
    best_accuracy = 0
    results = []

    for n in num_qubits_list:
        target_state = bin((1 << n) - 1)[2:]
        for num_iterations in num_iterations_list:
            counts, execution_time = run_grover_test(n, target_state, num_iterations, shots)
            accuracy = counts.get(target_state, 0) / shots
            results.append({
                'num_qubits': n,
                'num_iterations': num_iterations,
                'target_state': target_state,
                'counts': counts,
                'accuracy': accuracy,
                'execution_time': execution_time
            })
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_config = (n, num_iterations)
            
            print(f'Test with {n} qubits, {num_iterations} iterations, target state {target_state}')
            print(f'Counts: {counts}')
            print(f'Accuracy: {accuracy:.4f}')
            print(f'Execution time: {execution_time:.4f} seconds\n')

            # Plotting the histogram
            plt.figure()
            plot_histogram(counts)
            plt.title(f'{n} Qubits, {num_iterations} Iterations, Target {target_state}')
            plt.savefig(f'grover_results_{n}qubits_{num_iterations}iterations.png')
            plt.close()

    print(f'Best configuration: {best_config} with accuracy: {best_accuracy:.4f}')

    # Save the results to a file
    with open('etpt_algorithm_optimization_results.txt', 'w') as f:
        for result in results:
            f.write(f'{result}\n')

if __name__ == '__main__':
    optimize_etpt_algorithm()
