"""
nab_to_vm.py

Convert Numenta NAB CSVs (timestamp,value) into Influx Line Protocol and
optionally push to VictoriaMetrics (/write).

Usage examples:
  # dry-run: convert CSVs to .lp files in ./out_lp
  python nab_to_vm.py --input-dir ./nab_csvs --out-dir ./out_lp

  # push directly to local VictoriaMetrics in batches
  python nab_to_vm.py --input-dir ./nab_csvs --vm-url http://localhost:8428 --push

Options:
  --metric-prefix  prefix for metric name (default: nab)
  --time-format    python strptime format for your timestamps (default: "%Y-%m-%d %H:%M:%S")
  --timezone       timezone for timestamps (default: "UTC")  # currently informational
  --batch-size     number of lines per POST (default: 5000)
"""
import os
import argparse
import csv
from datetime import datetime, timezone, timedelta
import requests

def escape_lp(s: str) -> str:
    # minimal escaping for measurement/tag keys/values per Influx line protocol:
    return s.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")

def csv_to_lines(csv_path: str, metric_prefix: str, host_tag: str,
                 time_fmt: str) -> list:
    lines = []
    with open(csv_path, "r", newline='') as fh:
        reader = csv.DictReader(fh)
        if "timestamp" not in reader.fieldnames or "value" not in reader.fieldnames:
            raise ValueError(f"{csv_path}: expected header 'timestamp,value'")
        for row in reader:
            ts_str = row["timestamp"].strip()
            val_str = row["value"].strip()
            if ts_str == "" or val_str == "":
                continue
            # parse timestamp (assume given format, default: "%Y-%m-%d %H:%M:%S")
            dt = datetime.strptime(ts_str, time_fmt) + timedelta(days=150)
            # treat as UTC (if your CSV is local, adjust accordingly)
            dt = dt.replace(tzinfo=timezone.utc)
            ts_ns = int(dt.timestamp() * 1_000_000_000)  # nanoseconds
            # measurement name: metric_prefix + "_" + basename
            measurement = escape_lp(metric_prefix)
            tag_part = f'host={escape_lp(host_tag)}'
            # value is float
            try:
                float_val = float(val_str)
            except:
                # skip non-numeric
                continue
            # Influx LP: measurement,tagk=tagv field=123 123000000000
            line = f"{measurement},{tag_part} value={float_val} {ts_ns}"
            lines.append(line)
    return lines

def push_batch(vm_write_url: str, batch_lines: list, verify_ssl=True):
    payload = "\n".join(batch_lines) + "\n"
    # POST to /write
    url = vm_write_url.rstrip("/") + "/write"
    resp = requests.post(url, data=payload)
    if resp.status_code not in (200,204):
        raise RuntimeError(f"POST {url} returned {resp.status_code}: {resp.text}")
    return resp.status_code

def process_dir(input_dir: str, out_dir: str, vm_url: str, push: bool,
                metric_prefix: str, batch_size: int, time_fmt: str):
    files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(".csv")])
    if not files:
        raise SystemExit("No .csv files found in input directory")
    os.makedirs(out_dir, exist_ok=True)
    for fname in files:
        csv_path = os.path.join(input_dir, fname)
        host = os.path.splitext(fname)[0]
        print(f"[+] Processing {csv_path}  -> host='{host}'")
        lines = csv_to_lines(csv_path, metric_prefix, host, time_fmt)
        if not lines:
            print("  (no lines generated, skipping)")
            continue

        # either write .lp file or push in batches
        lp_path = os.path.join(out_dir, f"{host}.lp")
        with open(lp_path, "w") as outfh:
            outfh.write("\n".join(lines) + ("\n" if lines else ""))

        print(f"  Wrote {len(lines)} lines to {lp_path}")
        if push:
            print("  Pushing to VictoriaMetrics in batches...")
            for i in range(0, len(lines), batch_size):
                batch = lines[i:i+batch_size]
                push_batch(vm_url, batch)
            print("  Push completed.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True, help="folder with CSV files")
    p.add_argument("--out-dir", default="./out_lp", help="where to write .lp files")
    p.add_argument("--vm-url", default="http://localhost:8428", help="VictoriaMetrics URL")
    p.add_argument("--push", action="store_true", help="POST data to VM /write")
    p.add_argument("--metric-prefix", default="nab", help="metric name prefix")
    p.add_argument("--batch-size", default=5000, type=int, help="lines per POST")
    p.add_argument("--time-format", default="%Y-%m-%d %H:%M:%S", help="python strptime format")
    args = p.parse_args()
    process_dir(args.input_dir, args.out_dir, args.vm_url, args.push,
                args.metric_prefix, args.batch_size, args.time_format)

if __name__ == "__main__":
    main()
