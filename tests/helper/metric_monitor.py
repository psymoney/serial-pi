import argparse
import psutil
import time
import json


def monitor_pid(
    pid: int,
    interval: float = 1.0,
    duration: float = -1.0,
    output_file: str = "default.log",
):
    try:
        p = psutil.Process(pid)
    except psutil.NoSuchProcess:
        print(f"Process {pid} does not exist.")
        return

    start = time.time()
    metrics = []
    with open(output_file, "a", encoding="utf-8") as f:
        while duration < 0 or time.time() - start < duration:
            with p.oneshot():
                cpu = p.cpu_percent(interval=None)
                mem = p.memory_info().rss
                io = p.io_counters()
                threads = p.num_threads()

            data = {
                "timestamp": time.time(),
                "cpu_percent": cpu,
                "memory_rss": mem,
                "read_counts": io.read_count,
                "write_counts": io.write_count,
                "read_bytes": io.read_bytes,
                "write_bytes": io.write_bytes,
                "num_threads": threads,
            }
            metrics.append(data)
            f.write(json.dumps(data) + "\n")
            f.flush()
            time.sleep(interval)


if __name__ == "__main__":
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pid", type=int, required=True, help="PID to monitor")
    parser.add_argument("--id", type=str, required=True, help="Output file name")
    parser.add_argument(
        "-f", "--file", type=str, required=True, help="Output file name"
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=1.0, help="Sampling interval"
    )
    parser.add_argument(
        "-d", "--duration", type=float, default=-1.0, help="Monitoring duration"
    )
    args = parser.parse_args()

    result_path = Path(__file__).parent.parent / "perf" / "results" / args.id
    result_path.mkdir(parents=True, exist_ok=True)
    file_name = result_path / args.file

    monitor_pid(args.pid, args.interval, args.duration, file_name)
