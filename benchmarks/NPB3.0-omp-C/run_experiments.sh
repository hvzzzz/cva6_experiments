#!/bin/sh

# ==============================================================================
#  CVA6 FPGA AUTOMATED BENCHMARK SUITE (NPB ONLY)
#  Runs NAS Parallel Benchmarks with PAPI instrumentation
# ==============================================================================

# --- Configuration ---
# 1. Path to your NPB binaries (Adjust if different)
NPB_DIR="./bin"

# 2. Output File
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTFILE="NPB_${TIMESTAMP}.txt"

# --- Setup ---
echo "Setting up permissions..."
echo -1 >/proc/sys/kernel/perf_event_paranoid

# --- Helper Function ---
run_test() {
    NAME="$1"
    CMD="$2"

    echo "--------------------------------------------------"
    echo "Running: $NAME"

    # 1. Print Start Delimiter for Python Parser
    echo ">>>BEGIN_TEST|$NAME" >>"$OUTFILE"

    # 2. Execute Command
    if [ -f "$CMD" ]; then
        $CMD >>"$OUTFILE" 2>&1
    else
        echo "Error: Binary not found: $CMD" >>"$OUTFILE"
        echo "Error: Binary not found: $CMD"
    fi

    # 3. Print End Delimiter
    echo ">>>END_TEST" >>"$OUTFILE"
    echo "" >>"$OUTFILE"
}

# ==============================================================================
#  MAIN EXECUTION
# ==============================================================================

# 1. Write Metadata Header
echo "METADATA|Date|$(date)" >"$OUTFILE"
echo "METADATA|Kernel|$(uname -r)" >>"$OUTFILE"
echo "METADATA|CPU Info|" >>"$OUTFILE"
cat /proc/cpuinfo >>"$OUTFILE" 2>&1
echo "=============================================" >>"$OUTFILE"

echo "Starting NPB Suite..."
echo "Results will be saved to: $OUTFILE"

# --- 1. Compute Intensive ---
# EP (Embarrassingly Parallel):
# - Does almost zero communication/memory.
# - Pure FPU/ALU stress test.
# - EXPECT: Highest IPC of the suite.
run_test "NPB_EP_S" "$NPB_DIR/ep.S"

# --- 2. Memory Intensive (Random Access) ---
# IS (Integer Sort):
# - Random memory access pattern (Bucket sort).
# - Stresses TLB and Cache Miss penalties.
# - EXPECT: Lowest IPC (Memory Bound).
run_test "NPB_IS_S" "$NPB_DIR/is.S"

# CG (Conjugate Gradient):
# - Sparse matrix-vector multiplication.
# - Irregular memory access + Floating point.
# - EXPECT: Low IPC.
run_test "NPB_CG_S" "$NPB_DIR/cg.S"

# --- 3. Memory Intensive (Structured/Streaming) ---
# MG (Multi-Grid):
# - Solves 3D Poisson equation.
# - Strided memory access (predictable but heavy).
# - EXPECT: Medium IPC.
run_test "NPB_MG_S" "$NPB_DIR/mg.S"

# FT (Fourier Transform):
# - Heavy 3D array transposition.
# - Streaming memory access.
run_test "NPB_FT_S" "$NPB_DIR/ft.S"

# --- 4. Pseudo-Applications (Solver Kernels) ---
# These mimic real-world CFD applications.
# They test the balance between Compute and Memory.

# BT (Block Tridiagonal):
# - Solves block-tridiagonal matrices.
# - Good data locality (cache friendly).
run_test "NPB_BT_S" "$NPB_DIR/bt.S"

# SP (Scalar Pentadiagonal):
# - Solves pentadiagonal matrices.
# - Less cache friendly than BT.
run_test "NPB_SP_S" "$NPB_DIR/sp.S"

# LU (Lower-Upper Gauss-Seidel):
# - Solver.
run_test "NPB_LU_S" "$NPB_DIR/lu.S"

# ==============================================================================
#  FINISH
# ==============================================================================
echo "============================================="
echo "   SUITE COMPLETE"
echo "   Please download: $OUTFILE"
echo "============================================="
