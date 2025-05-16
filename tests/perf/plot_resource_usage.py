from os import path
from textwrap import indent
import matplotlib.pyplot as plt
import json
import re
import argparse
import pathlib
from datetime import datetime


def parse_log(file_path):
    timestamps, cpu_usages, rss_usages = [], [], []
    label = None
    with open(file_path) as f:
        for line in f:
            j = json.loads(line)

            print(j)
            # match = re.match(
            #     r"(\w+)\s+(\d+\.\d+)\s+CPU=(\d+\.\d+)\s+RSS=(\d+)", line)
            # if not match:
            #     continue
            # label, ts, cpu, rss = match.groups()
            timestamps.append(float(j.get('timestamp')))
            cpu_usages.append(float(j.get('cpu_percent')))
            rss_usages.append(int(j.get('memory_rss')) / 1024 / 1024)  # convert to MB

    return label, timestamps, cpu_usages, rss_usages


def normalize_timestamps(timestamps):
    base = timestamps[0]
    return [t - base for t in timestamps]


def plot_metric(title, ylabel, async_x, async_y, block_x, block_y, save_as=None):
    plt.figure(figsize=(10, 4))
    plt.plot(async_x, async_y, label="Async", color="tab:blue")
    plt.plot(block_x, block_y, label="Blocking", color="tab:orange")
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    if save_as:
        plt.savefig(save_as, dpi=200, bbox_inches="tight")
    else:
        plt.show()
    plt.close()


def main(async_log, block_log):
    async_label, async_ts, async_cpu, async_rss = parse_log(async_log)
    block_label, block_ts, block_cpu, block_rss = parse_log(block_log)
    print(parse_log(async_log))
    print(parse_log(block_log))
    async_ts = normalize_timestamps(async_ts)
    block_ts = normalize_timestamps(block_ts)

    plot_metric(
        "CPU Usage Over Time",
        "CPU (%)",
        async_ts,
        async_cpu,
        block_ts,
        block_cpu,
        "cpu_comparison.png",
    )
    plot_metric(
        "Memory Usage Over Time",
        "RSS (MB)",
        async_ts,
        async_rss,
        block_ts,
        block_rss,
        "rss_comparison.png",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id", required=True, type=str)
    parser.add_argument("--async_log", default="async_metric.txt")
    parser.add_argument("--block_log", default="blocking_metric.txt")
    args = parser.parse_args()

    base_path = pathlib.Path(__file__).parent / "results"
    async_path = base_path / args.id / args.async_log
    blocking_path = base_path / args.id / args.block_log

    main(async_path, blocking_path)
