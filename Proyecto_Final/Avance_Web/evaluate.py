"""
Fase 3 — Evaluation script.
Runs smart_process on each image in ground_truth.csv and measures per-field precision.

Usage:
    uv run python evaluate.py [--gt ground_truth.csv] [--receipts receipts/]
"""
import csv
import os
import sys
import argparse
import json

from app import smart_process  # initializes EasyOCR reader on import (~5s cold start)

# ────────────────────────────────────────────────────────────────────────────

FIELDS = ["Comercio", "Fecha", "Moneda", "Impuestos", "Total"]


def partial_match(pred, gt):
    """True if either string contains the other (case-insensitive, whitespace-normalized).
    Also checks if first significant word of gt appears in pred."""
    if not pred or not gt:
        return False
    import re
    p = re.sub(r'\s+', ' ', pred.strip().lower())
    g = re.sub(r'\s+', ' ', gt.strip().lower())
    if p in g or g in p:
        return True
    # Word-level: first meaningful word of gt (len>3, no abbreviations) in pred
    gt_words = [w for w in g.split() if len(w) > 3 and '.' not in w][:1]
    return bool(gt_words) and all(w in p for w in gt_words)


def exact_match(pred, gt):
    return pred.strip().lower() == gt.strip().lower()


def evaluate(gt_path, receipts_dir):
    rows = []
    with open(gt_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    counts = {field: {"hit": 0, "partial": 0, "miss": 0, "skip": 0} for field in FIELDS}
    results = []

    for row in rows:
        fname = row["file"]
        img_path = os.path.join(receipts_dir, fname)
        if not os.path.exists(img_path):
            print(f"[SKIP] {fname} — not found")
            for f in FIELDS:
                if row.get(f, "").strip():
                    counts[f]["skip"] += 1
            continue

        print(f"[RUN ] {fname} ...", end=" ", flush=True)
        try:
            res = smart_process(img_path)
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        if res is None:
            print("→ pipeline returned None")
            continue

        pred = res["parsed_info"]
        row_result = {"file": fname, "predicted": pred, "gt": {}, "match": {}}

        for field in FIELDS:
            gt_val = row.get(field, "").strip()
            pred_val = pred.get(field, "").strip()
            row_result["gt"][field] = gt_val
            if not gt_val:
                counts[field]["skip"] += 1
                row_result["match"][field] = "skip"
                continue
            if exact_match(pred_val, gt_val):
                counts[field]["hit"] += 1
                row_result["match"][field] = "exact"
            elif partial_match(pred_val, gt_val):
                counts[field]["partial"] += 1
                row_result["match"][field] = "partial"
            else:
                counts[field]["miss"] += 1
                row_result["match"][field] = f"MISS (got={pred_val!r})"

        results.append(row_result)
        summary = "  ".join(
            f"{f}:{row_result['match'].get(f,'?')}" for f in FIELDS
        )
        print(f"→ {summary}")

    # ── Summary table ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"{'FIELD':<12} {'EXACT':>6} {'PARTIAL':>8} {'MISS':>6} {'SKIP':>6} {'PREC%':>7}")
    print("-" * 60)
    total_exact = total_partial = total_miss = 0
    for field in FIELDS:
        c = counts[field]
        evaluated = c["hit"] + c["partial"] + c["miss"]
        prec = ((c["hit"] + 0.5 * c["partial"]) / evaluated * 100) if evaluated else 0
        print(
            f"{field:<12} {c['hit']:>6} {c['partial']:>8} {c['miss']:>6} "
            f"{c['skip']:>6} {prec:>6.1f}%"
        )
        total_exact += c["hit"]
        total_partial += c["partial"]
        total_miss += c["miss"]

    total_evaluated = total_exact + total_partial + total_miss
    overall = ((total_exact + 0.5 * total_partial) / total_evaluated * 100) if total_evaluated else 0
    print("=" * 60)
    print(f"OVERALL PRECISION (exact=1, partial=0.5): {overall:.1f}%  "
          f"({total_exact}E + {total_partial}P + {total_miss}M / {total_evaluated} evaluated)")

    # Save JSON report
    report_path = "eval_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"counts": counts, "results": results, "overall_pct": round(overall, 1)}, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed report → {report_path}")
    return overall


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt", default="ground_truth.csv")
    parser.add_argument("--receipts", default="receipts")
    args = parser.parse_args()
    evaluate(args.gt, args.receipts)
