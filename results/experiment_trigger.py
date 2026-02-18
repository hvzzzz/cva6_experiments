import serial
import time
import paramiko
import re
import csv
import os
import subprocess

# ================= CONFIGURATION =================
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
BOOT_TIMEOUT = 1200
POST_KERNEL_NAP = 100
BENCHMARK_WATCHDOG = 1200

SSH_HOST = "192.168.1.99"
SSH_USER = "xilinx"
REMOTE_SWEEP_DIR = "sweep"

KERNEL_START_SIGNALS = ["Linux version", "SBI specification", "[    0.000000]"]
PROBE_CODE = "ARIANE_PING"
CSV_FILENAME = "sweep_results_final_3.csv"
# =================================================


def run_local_command(cmd_list):
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"    Local command failed: {e}")
        return False


def recover_network():
    print("\n[Network] Waiting 20 seconds for remote reboot...")
    time.sleep(20)
    print("[Network] Attempting to bring up wired connection (PYNQ)...")
    while True:
        success = run_local_command(["nmcli", "connection", "up", "PYNQ"])
        if success:
            print("[Network] SUCCESS: Connection 'PYNQ' is active.")
            break
        else:
            print("[Network] FAILED. Retrying in 5 seconds...")
            time.sleep(5)


def reboot_ssh_host(ssh):
    print("\n[SSH] Sending reboot command to 192.168.1.99...")
    try:
        ssh.exec_command("sudo reboot now")
    except Exception:
        pass
    ssh.close()
    print("[SSH] Connection closed. Reboot initiated.")


def create_ssh_client():
    retries = 0
    while True:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                SSH_HOST,
                username=SSH_USER,
                look_for_keys=True,
                allow_agent=True,
                timeout=10,
            )
            return client
        except Exception as e:
            if retries == 0:
                print(f"[SSH] Waiting for host to come online... ({e})")
            time.sleep(5)
            retries += 1


def get_bitstream_list():
    print(f"[Setup] Connecting to list files in '{REMOTE_SWEEP_DIR}'...")
    ssh = create_ssh_client()
    cmd = f"cd {REMOTE_SWEEP_DIR} && ls *.bit.bin"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    file_list = []
    for line in stdout:
        filename = line.strip()
        if filename:
            file_list.append(filename)
    ssh.close()
    file_list.sort()
    print(f"[Setup] Found {len(file_list)} bitstreams.")
    return file_list


def slow_write(ser, text, delay=0.3):
    for char in text:
        ser.write(char.encode("utf-8"))
        time.sleep(delay)


def clean_buffer(ser):
    if ser.in_waiting:
        ser.read(ser.in_waiting)


def wait_for_prompt(ser, timeout=10):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            if "#" in chunk or ">" in chunk:
                return True
        time.sleep(0.1)
    return False


def sync_time(ser):
    print("[Task] Synchronizing Time...")
    host_time = int(time.time())

    clean_buffer(ser)
    slow_write(ser, f"date -s @{host_time}\r")

    if not wait_for_prompt(ser, timeout=10):
        print("       [Warning] Timeout waiting for date command prompt.")

    clean_buffer(ser)
    slow_write(ser, "date '+%s'\r")

    time.sleep(1)
    listen_end = time.time() + 5
    device_time_str = ""
    while time.time() < listen_end:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            device_time_str += chunk
            if "#" in chunk:
                break
        time.sleep(0.1)
    match = re.search(r"(\d{10})", device_time_str)
    if match:
        diff = abs(int(match.group(1)) - host_time)
        if diff <= 10:
            print(f"       Success (Diff: {diff}s)")
            return True
    print(f"       Failed to sync time.")
    return False


def run_benchmark_generic(ser, task_name, command, file_regex_1, file_regex_2=None):
    print(f"[Task] Running {task_name}...")

    ser.reset_input_buffer()
    slow_write(ser, command)

    captured_filename = "ERROR"
    experiment_running = True
    last_activity_time = time.time()
    line_buffer = ""

    finish_deadline = None

    # --- PHASE 1: ECHO CONSUMPTION + EARLY SCAN ---
    print("       (Consuming command echo & scanning early output...)")
    echo_end_time = time.time() + 5
    while time.time() < echo_end_time:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            line_buffer += chunk
            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                line = line.strip()
                if file_regex_1 in line:
                    match = re.search(rf"{file_regex_1}\s+([\w\d_\.]+\.txt)", line)
                    if match:
                        captured_filename = match.group(1)
                        print(
                            f"\n[INFO] Captured Filename (Early): {captured_filename}"
                        )
        time.sleep(0.1)

    # --- PHASE 2: MAIN MONITORING ---
    print("       (Monitoring execution...)")
    while experiment_running:
        if ser.in_waiting:
            last_activity_time = time.time()
            chunk = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            print(chunk, end="", flush=True)

            line_buffer += chunk

            # Process complete lines
            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                line = line.strip()

                # Check Filenames
                if file_regex_1 in line:
                    match = re.search(rf"{file_regex_1}\s+([\w\d_\.]+\.txt)", line)
                    if match:
                        captured_filename = match.group(1)
                        print(f"\n[INFO] Captured Filename: {captured_filename}")

                if file_regex_2 and file_regex_2 in line:
                    match = re.search(rf"{file_regex_2}\s+([\w\d_\.]+\.txt)", line)
                    if match and captured_filename == "ERROR":
                        captured_filename = match.group(1)

                # Check for Completion
                if "SUITE COMPLETE" in line:
                    if finish_deadline is None:
                        finish_deadline = time.time() + 20
                        print(
                            f"\n[INFO] Suite finished. Waiting 20s for trailing data..."
                        )

                # Check for Shell Prompt
                if line.endswith("#") or line == "#":
                    if finish_deadline is None:
                        print(f"\n[INFO] Shell prompt detected. {task_name} finished.")
                        finish_deadline = time.time() + 1  # Exit quickly if prompt seen

        else:
            # Watchdog check
            if (time.time() - last_activity_time) > BENCHMARK_WATCHDOG:
                print(
                    f"\n[FAILURE] Watchdog Timeout! No output for {BENCHMARK_WATCHDOG}s. Assuming HANG."
                )
                return "HANG_TIMEOUT"

        # Check Finish Deadline
        if finish_deadline and time.time() > finish_deadline:
            experiment_running = False

        time.sleep(0.1)

    return captured_filename


def run_benchmark_cycle(ser, ssh, bitstream_file):
    print("\n" + "=" * 60)
    print(f"CYCLE START: {bitstream_file}")
    print("=" * 60)

    print(f"[Step 1] Flashing bitstream...")
    cmd = f"sudo ./flash_bin {REMOTE_SWEEP_DIR}/{bitstream_file}"
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"[Error] Flashing failed: {stderr.read().decode()}")
        return "FLASH_FAIL", "FLASH_FAIL"
    print("[Step 1] Flash complete. System Rebooting...")

    print("[Step 2] Waiting for Kernel...")
    ser.reset_input_buffer()
    start_time = time.time()
    kernel_started = False
    while (time.time() - start_time) < BOOT_TIMEOUT:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            for sig in KERNEL_START_SIGNALS:
                if sig in chunk:
                    kernel_started = True
                    break
            if kernel_started:
                break
        time.sleep(0.1)

    if not kernel_started:
        print("\n[FAILURE] Boot Timeout: Kernel start signal never detected.")
        return "BOOT_TIMEOUT", "BOOT_TIMEOUT"

    print(f"[Step 3] Nap time ({POST_KERNEL_NAP}s)...")
    time.sleep(POST_KERNEL_NAP)
    clean_buffer(ser)

    print("[Step 4] Probing Shell...")
    probe_start = time.time()
    shell_confirmed = False

    while (time.time() - probe_start) < 600:
        ser.reset_input_buffer()
        slow_write(ser, f"\r")
        time.sleep(1)
        if ser.in_waiting:
            resp = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            if "#" in resp:
                print("         Shell Ready (Prompt detected)!")
                shell_confirmed = True
                break
            slow_write(ser, f"echo {PROBE_CODE}\r")
            time.sleep(1)
            if ser.in_waiting:
                resp = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
                if PROBE_CODE in resp and "#" in resp:
                    print("         Shell Ready (Echo+Prompt detected)!")
                    shell_confirmed = True
                    break
        time.sleep(5)

    if not shell_confirmed:
        return "SHELL_FAIL", "SHELL_FAIL"

    time.sleep(2)
    sync_time(ser)

    time.sleep(2)
    npb_res = run_benchmark_generic(
        ser,
        task_name="NPB Suite",
        command="cd scratch/hvzzzz/NPB3.0-omp-C/ && ./run_experiments.sh\r",
        file_regex_1="Results will be saved to:",
        file_regex_2="Please download:",
    )

    if npb_res == "HANG_TIMEOUT":
        return "HANG_TIMEOUT", "SKIPPED"

    time.sleep(2)
    unix_res = run_benchmark_generic(
        ser,
        task_name="UnixBench",
        command="cd ../UnixBench/ && ./run_experiments.sh\r",
        file_regex_1="Output File:",
        file_regex_2="Results saved to:",
    )

    return npb_res, unix_res


def main():
    file_exists = os.path.isfile(CSV_FILENAME)
    csv_file = open(CSV_FILENAME, "a", newline="")
    writer = csv.writer(csv_file)
    if not file_exists:
        writer.writerow(["Bitstream", "NPB_File", "UnixBench_File"])
        csv_file.flush()

    try:
        bitstreams = get_bitstream_list()
        print(f"Opening Serial Port {SERIAL_PORT}...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)

        # NOTE: Restarting from the very beginning (0)
        for i, bitstream in enumerate(bitstreams):
            print(f"\n--- Progress: {i + 1}/{len(bitstreams)} ---")
            print("[System] Connecting to SSH Host...")
            ssh = create_ssh_client()

            try:
                npb, unix = run_benchmark_cycle(ser, ssh, bitstream)
                writer.writerow([bitstream, npb, unix])
                csv_file.flush()
                reboot_ssh_host(ssh)
                recover_network()
            except Exception as e:
                print(f"[CRITICAL ERROR] Failed on {bitstream}: {e}")
                writer.writerow([bitstream, "ERROR", str(e)])
                csv_file.flush()
                try:
                    reboot_ssh_host(ssh)
                except:
                    pass
                recover_network()

    except KeyboardInterrupt:
        print("\nStopping automation...")
    finally:
        csv_file.close()
        if "ser" in locals() and ser.is_open:
            ser.close()
        print(f"Results saved to {CSV_FILENAME}")


if __name__ == "__main__":
    main()
