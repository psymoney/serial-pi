import re
import matplotlib.pyplot as plt
import json
import argparse
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
from itertools import cycle


_color_cycle = cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])


@lru_cache(maxsize=None)
def get_color_for_mode(mode: str) -> str:
    return next(_color_cycle)


def parse_log(file_path):
    timestamps, cpu_usages, rss_usages = [], [], []
    read_counts, write_counts = [], []
    read_bytes, write_bytes, num_threads = [], [], []

    with open(file_path) as f:
        for line in f:
            j = json.loads(line)
            timestamps.append(float(j.get("timestamp")))
            cpu_usages.append(float(j.get("cpu_percent")))
            rss_usages.append(int(j.get("memory_rss")) / 1024 / 1024)  # convert to MB
            read_counts.append(int(j.get("read_counts")))
            write_counts.append(int(j.get("write_counts")))
            read_bytes.append(int(j.get("read_bytes")))
            write_bytes.append(int(j.get("write_bytes")))
            num_threads.append(int(j.get("num_threads")))

    return timestamps, cpu_usages, rss_usages, read_counts, write_counts, read_bytes, write_bytes, num_threads


def normalize_timestamps(timestamps):
    base = timestamps[0]
    return [t - base for t in timestamps]


def plot_dual_axis_metric(
    time_data: dict,
    left_metric_data: dict,
    right_metric_data: dict,
    left_label: str = "Left Metric",
    right_label: str = "Right Metric",
    title: str = "Metric Comparison",
    save_as: Path = None,
):
    plt.figure(figsize=(10, 4))
    ax1 = plt.gca()
    ax2 = ax1.twinx()

    modes = sorted(set(left_metric_data.keys()) | set(right_metric_data.keys()))

    for mode in modes:
        color = get_color_for_mode(mode)
        if mode in left_metric_data:
            ax1.plot(
                time_data[mode],
                left_metric_data[mode],
                label=f"{mode} - {left_label}",
                color=color,
                linestyle="-",
            )
        if mode in right_metric_data:
            ax2.plot(
                time_data[mode],
                right_metric_data[mode],
                label=f"{mode} - {right_label}",
                color=color,
                linestyle="--",
            )

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel(left_label)
    ax2.set_ylabel(right_label)

    ax1.grid(True)

    # 범례 병합
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    plt.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

    plt.title(title)
    if save_as:
        plt.savefig(save_as, dpi=200, bbox_inches="tight")
    else:
        plt.show()

    plt.close()


def plot_metric(title, ylabel, x_data: dict, y_data: dict, save_as=None):
    plt.figure(figsize=(10, 4))
    for mode, y in y_data.items():
        plt.plot(x_data[mode], y, label=mode.capitalize())
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


def make_readme(readme_path, averages: dict):
    metrics = ["cpu_percent", "memory_rss", "read_bytes", "write_bytes", "num_threads"]
    labels = {
        "cpu_percent": "CPU (%)",
        "memory_rss": "RSS (MB)",
        "read_bytes": "Read (MB)",
        "write_bytes": "Write (MB)",
        "num_threads": "Threads",
    }

    readme_lines = [
        "# metric graph",
        "",
        "![cpu](./img/cpu_comparison.png)",
        "![rss](./img/rss_comparison.png)",
        "![read](./img/read_comparison.png)",
        "![write](./img/write_comparison.png)",
        "![threads](./img/threads_comparison.png)",
        "",
        "## 평균 사용량 (Average Usage)",
        "",
        "| Mode | " + " | ".join(labels[m] for m in metrics) + " |",
        "|------" + "|--------------" * len(metrics) + "|",
    ]
    modes = sorted(averages["cpu_percent"].keys())
    for mode in modes:
        row = [f"{averages[m][mode]:.2f}" for m in metrics]
        readme_lines.append(f"| {mode} | " + " | ".join(row) + " |")

    readme_path.write_text("\n".join(readme_lines), encoding="utf-8")


def parse_filename(filename: str) -> tuple[str, str]:
    match = re.match(r"(?P<mode>\w+?)_(?P<params>.+)\.log", filename)
    if not match:
        return None, None
    mode = match.group("mode")
    params_str = match.group("params")
    return mode, params_str


def summarize_results(dir: Path):
    log_files = list(dir.glob("*.log"))
    result_groups = defaultdict(dict)

    for f in log_files:
        mode, param_str = parse_filename(f.name)
        if not param_str:
            continue

        result_groups[param_str][mode] = f

    readme_lines = [
        "# Metric Graphs",
        "",
        "## Overview",
        "",
    ]

    for param_str, files in sorted(result_groups.items()):
        cpu = defaultdict(list)
        rss = defaultdict(list)
        time = defaultdict(list)
        read_count = defaultdict(list)
        write_count = defaultdict(list)
        threads = defaultdict(list)

        avg_cpu = defaultdict(float)
        avg_rss = defaultdict(float)
        avg_read_cnt = defaultdict(float)
        avg_write_cnt = defaultdict(float)
        total_read_bytes = defaultdict(int)
        total_write_bytes = defaultdict(int)
        avg_threads = defaultdict(float)

        for mode, path in files.items():
            timestamps, cpu_, rss_, rc, wc, read_, write_, threads_ = parse_log(path)

            time[mode] = normalize_timestamps(timestamps)
            cpu[mode] = cpu_
            rss[mode] = rss_
            read_count[mode] = rc
            write_count[mode] = wc
            threads[mode] = threads_

            avg_cpu[mode] = sum(cpu_) / len(cpu_) if cpu_ else 0.0
            avg_rss[mode] = sum(rss_) / len(rss_) if rss_ else 0.0
            avg_read_cnt[mode] = sum(rc) / len(rc) if rc else 0
            avg_write_cnt[mode] = sum(wc) / len(wc) if wc else 0
            total_read_bytes[mode] = max(read_)
            total_write_bytes[mode] = max(write_)
            avg_threads[mode] = sum(threads_) / len(threads_) if threads_ else 0.0

        if len(cpu) < 2:
            print(f"[!] Not enough modes for {param_str}. Skipping plot")
            continue

        img_dir = dir / "img" / param_str
        img_dir.mkdir(parents=True, exist_ok=True)

        plot_dual_axis_metric(
            time_data=time,
            left_metric_data=cpu,
            right_metric_data=rss,
            left_label="CPU (%)",
            right_label="RSS (MB)",
            title=f"CPU & Memory Usage Over Time ({param_str})",
            save_as=img_dir / "cpu_rss_comparison",
        )
        plot_dual_axis_metric(
            time_data=time,
            left_metric_data=read_count,
            right_metric_data=write_count,
            left_label="Read Count",
            right_label="Write Count",
            title="Disk I/O Over Time",
            save_as=img_dir / "io_comparision.png",
        )

        print(f"[✓] Plots for {param_str} saved to {img_dir}")

        readme_lines.extend(
            [
                f"### Params: `{param_str}`",
                "",
                f"![CPU&RSS](./img/{param_str}/cpu_rss_comparison.png)",
                f"![READ&WRITE](./img/{param_str}/io_comparision.png)",
                "",
                "| Mode | Avg CPU (%) | Avg RSS (MB) | Total Read Bytes | Total Write Bytes | Avg Read Count | Avg Write Count | Avg # of Threads |",
                "|------|-------------|--------------|------------------|-------------------|----------------|-----------------|------------------|",
            ]
        )
        for mode in sorted(avg_cpu.keys()):
            readme_lines.append(
                f"| {mode} | {avg_cpu[mode]:.2f} | {avg_rss[mode]:.2f} | {total_read_bytes[mode]:.1f} | {total_write_bytes[mode]:.1f} | {avg_read_cnt[mode]:.1f} | {avg_write_cnt[mode]:.1f} | {avg_threads[mode]:.1f} |"
            )
        readme_lines.append("")

    readme_path = dir / "README.md"
    readme_path.write_text("\n".join(readme_lines), encoding="utf-8")
    # make_readme(dir / "README.md", avg_cpu, avg_rss)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id", required=True, type=Path)
    args = parser.parse_args()

    summarize_results(args.id)
