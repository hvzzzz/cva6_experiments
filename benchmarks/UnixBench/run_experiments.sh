#!/bin/sh

# --- Configuration ---
# File to save results to
OUTFILE="unixbench_$(date +%Y%m%d_%H%M%S).txt"
# Duration for time-based tests (seconds)
DUR=10
# Iterations for Whetstone (Floating point loops)
WHET_ITERS=3000000

# --- Setup ---
# Ensure we have permissions to read hardware counters
echo -1 >/proc/sys/kernel/perf_event_paranoid

# --- Helper Function ---
# Usage: run_test "Benchmark_Name" "Command"
run_test() {
  NAME="$1"
  CMD="$2"

  echo "Running: $NAME..."

  # 1. Print Start Delimiter for Parser
  echo ">>>BEGIN_TEST|$NAME" >>"$OUTFILE"

  # 2. Run the command and append stdout/stderr to file
  #$CMD >>"$OUTFILE" 2>&1
  $CMD 2>&1 | cat >>"$OUTFILE"

  # 3. Print End Delimiter
  echo ">>>END_TEST" >>"$OUTFILE"
  echo "" >>"$OUTFILE"
}

# --- Main Execution ---

echo "============================================="
echo "   STARTING CVA6 BENCHMARK SUITE"
echo "   Output File: $OUTFILE"
echo "============================================="

# Write Header Information
echo "METADATA|Date|$(date)" >"$OUTFILE"
echo "METADATA|Kernel|$(uname -r)" >>"$OUTFILE"
echo "METADATA|CPU Info|" >>"$OUTFILE"
cat /proc/cpuinfo >>"$OUTFILE"
echo "=============================================" >>"$OUTFILE"

# --- 1. Integer & CPU Intensive ---
run_test "Arithmetic_Overhead" "./pgms/arithoh $DUR"
run_test "Arithmetic_Register" "./pgms/register $DUR"
run_test "Arithmetic_Short" "./pgms/short $DUR"
run_test "Arithmetic_Int" "./pgms/int $DUR"
run_test "Dhrystone" "./pgms/dhry2reg $DUR"

# --- 2. Floating Point ---
run_test "Arithmetic_Double" "./pgms/double $DUR"
run_test "Whetstone" "./pgms/whetstone-double $WHET_ITERS"

# --- 3. System & Memory ---
run_test "Syscall_Mix" "./pgms/syscall $DUR mix"
run_test "Syscall_GetPID" "./pgms/syscall $DUR getpid"
run_test "Syscall_Exec" "./pgms/syscall $DUR exec"
run_test "Pipe_Throughput" "./pgms/pipe $DUR"
run_test "Context_Switching" "./pgms/context1 $DUR"

echo "============================================="
echo "   SUITE COMPLETE"
echo "   Results saved to: $OUTFILE"
echo "============================================="
