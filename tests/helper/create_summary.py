import matplotlib.pyplot as plt
import json
import argparse
import pathlib
from collections import defaultdict


def parse_log(file_path):
    timestamps, cpu_usages, rss_usages = [], [], []
    with open(file_path) as f:
        for line in f:
            j = json.loads(line)
            timestamps.append(float(j.get("timestamp")))
            cpu_usages.append(float(j.get("cpu_percent")))
            rss_usages.append(int(j.get("memory_rss")) / 1024 / 1024)  # convert to MB

    return timestamps, cpu_usages, rss_usages


def normalize_timestamps(timestamps):
    base = timestamps[0]
    return [t - base for t in timestamps]


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


def make_readme(readme_path, avg_cpu_dict, avg_rss_dict):
    readme_lines = [
        "# metric graph",
        "",
        "![cpu](./img/cpu_comparison.png)",
        "![rss](./img/rss_comparison.png)",
        "",
        "## 평균 사용량 (Average Usage)",
        "",
        "| Mode | Avg CPU (%) | Avg RSS (MB) |",
        "|------|--------------|---------------|"
    ]
    for mode in sorted(avg_cpu_dict.keys()):
        cpu = f"{avg_cpu_dict[mode]:.2f}"
        rss = f"{avg_rss_dict[mode]:.2f}"
        readme_lines.append(f"| {mode} | {cpu} | {rss} |")

    readme_path.write_text("\n".join(readme_lines), encoding="utf-8")


def main(
    id: str,
):
    base_path = pathlib.Path(__file__).parent / "results" / id
    img_dir = base_path / "img"
    img_dir.mkdir(exist_ok=True)

    log_files = list(base_path.glob("*.log"))

    cpu = defaultdict(list)
    rss = defaultdict(list)
    time = defaultdict(list)
    avg_cpu = {}
    avg_rss = {}

    for f in log_files:
        mode = f.stem.split("_")[0]
        timestamps, cpu_, rss_ = parse_log(f)
        time[mode] = normalize_timestamps(timestamps)
        cpu[mode] = cpu_
        rss[mode] = rss_
        avg_cpu[mode] = sum(cpu_) / len(cpu_) if cpu else 0.0
        avg_rss[mode] = sum(rss_) / len(rss_) if cpu else 0.0

    if len(cpu) >= 2:
        plot_metric(
            "CPU Usage Over Time",
            "CPU (%)",
            time,
            cpu,
            img_dir / "cpu_comparison.png",
        )
        plot_metric(
            "Memory Usage Over Time",
            "RSS (MB)",
            time,
            rss,
            img_dir / "rss_comparison.png",
        )
        print(f"[✓] Plots saved to {img_dir}")
    else:
        print("[!] At least two modes (e.g. async, block) are required for comparison.")

    make_readme(base_path / "README.md", avg_cpu, avg_rss)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id", required=True, type=str)
    args = parser.parse_args()

    main(args.id)
