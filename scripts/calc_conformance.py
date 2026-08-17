#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_conformance.py — 密评符合率计算与总体结论判定

用途：
    输入各测评项的判定结果（符合/部分符合/不符合/不适用），按权重计算
    符合率，并给出总体结论（符合/基本符合/不符合）。

输入方式（二选一）：
    1. JSON 文件 / 标准输入（推荐，可复用、可审计）：
         [
           {"item": "物理访问控制", "weight": 10, "result": "符合"},
           {"item": "传输机密性",   "weight": 15, "result": "部分符合"},
           {"item": "密钥存储",     "weight": 20, "result": "不符合"}
         ]
    2. 交互式逐项输入（不加 --json 参数时）。

评分规则（以 GM/T 0116-2021 官方文本为准，本脚本为可配置实现）：
    - 符合      -> 得 full 权重分
    - 部分符合  -> 得 weight * partial_ratio（默认 0.5）
    - 不符合    -> 得 0 分
    - 不适用    -> 不计入总权重（从分母中剔除）

结论阈值（默认，可用 --pass-rate / --fail-rate 覆盖，实际以标准为准）：
    - 符合率 >= pass_rate（默认 0.90）           -> 符合
    - 符合率 >= fail_rate（默认 0.60）           -> 基本符合
    - 否则                                      -> 不符合

用法：
    python calc_conformance.py --json results.json
    python calc_conformance.py --json results.json --pass-rate 0.85
    python calc_conformance.py                     # 交互模式
    echo '[{"item":"a","weight":10,"result":"符合"}]' | python calc_conformance.py --json -
"""

import argparse
import io
import json
import sys

# Windows 控制台默认 GBK，强制 stdout/stderr 使用 UTF-8 以支持 ⚠️ 等符号
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VALID_RESULTS = {"符合", "部分符合", "不符合", "不适用"}


def parse_items(text):
    """解析 JSON 输入为测评项列表。"""
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("JSON 必须是测评项数组")
    items = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ValueError(f"第 {i+1} 项不是对象")
        item = entry.get("item", f"测评项{i+1}")
        weight = entry.get("weight", 10)
        result = entry.get("result")
        if result not in VALID_RESULTS:
            raise ValueError(
                f"测评项 '{item}' 的 result 无效: {result!r}（可选: "
                + "/".join(sorted(VALID_RESULTS)) + "）"
            )
        if weight <= 0:
            raise ValueError(f"测评项 '{item}' 的 weight 必须为正数")
        items.append({"item": item, "weight": float(weight), "result": result})
    return items


def interactive_input():
    """交互式逐项录入。"""
    print("逐项录入测评结果（输入 q 结束）:")
    print(f"结果可选: {sorted(VALID_RESULTS)}")
    items = []
    while True:
        item = input("测评项名称: ").strip()
        if item.lower() == "q":
            break
        weight = input("权重(默认10): ").strip() or "10"
        result = input("判定结果: ").strip()
        if result not in VALID_RESULTS:
            print(f"无效判定，可选: {sorted(VALID_RESULTS)}")
            continue
        items.append({"item": item, "weight": float(weight), "result": result})
    return items


def compute(items, pass_rate, fail_rate):
    """计算符合率并判定总体结论。"""
    total_weight = 0.0
    earned = 0.0
    counts = {"符合": 0, "部分符合": 0, "不符合": 0, "不适用": 0}
    breakdown = []

    for it in items:
        w = it["weight"]
        r = it["result"]
        counts[r] += 1
        if r == "不适用":
            continue
        total_weight += w
        if r == "符合":
            earned += w
        elif r == "部分符合":
            earned += w * 0.5
        # 不符合得 0 分
        breakdown.append({"item": it["item"], "weight": w, "result": r})

    if total_weight <= 0:
        return {
            "error": "没有可计分的测评项（全部不适用或无数据）",
        }

    conformance = earned / total_weight

    if conformance >= pass_rate:
        conclusion = "符合"
    elif conformance >= fail_rate:
        conclusion = "基本符合"
    else:
        conclusion = "不符合"

    return {
        "total_items": len(items),
        "counts": counts,
        "effective_weight": total_weight,
        "earned_weight": earned,
        "conformance": round(conformance, 4),
        "conformance_percent": round(conformance * 100, 2),
        "pass_rate": pass_rate,
        "fail_rate": fail_rate,
        "conclusion": conclusion,
        "warnings": _warnings(counts),
    }


def _warnings(counts):
    """根据统计给出需要人工复核的提示。"""
    warns = []
    if counts["不符合"] > 0:
        warns.append(
            f"存在 {counts['不符合']} 个不符合项——请核查是否为红线问题"
            "（默认口令/明文密钥/无认证密码产品等），红线项可能直接否决总体结论"
        )
    if counts["部分符合"] > 0:
        warns.append(
            f"存在 {counts['部分符合']} 个部分符合项——请确认取证是否充分，"
            "部分符合的权重折算按 0.5 计，实际规则以 GM/T 0116 为准"
        )
    return warns


def format_report(res):
    """输出人类可读结果。"""
    lines = []
    lines.append("=" * 46)
    lines.append("密评符合率计算结果")
    lines.append("=" * 46)
    lines.append(f"测评项总数      : {res['total_items']}")
    c = res["counts"]
    lines.append(
        f"  符合 {c['符合']} ｜ 部分符合 {c['部分符合']} ｜ "
        f"不符合 {c['不符合']} ｜ 不适用 {c['不适用']}"
    )
    lines.append(f"参与计分权重    : {res['effective_weight']:.0f}")
    lines.append(f"实得权重        : {res['earned_weight']:.2f}")
    lines.append(f"符合率          : {res['conformance_percent']:.2f}%")
    lines.append(f"阈值(符合/基本) : {res['pass_rate']:.0%} / {res['fail_rate']:.0%}")
    lines.append(f"总体结论        : {res['conclusion']}")
    if res.get("warnings"):
        lines.append("-" * 46)
        lines.append("⚠️ 人工复核提示:")
        for w in res["warnings"]:
            lines.append(f"  - {w}")
    lines.append("=" * 46)
    lines.append("注：权重与判定规则以 GM/T 0116-2021 官方文本为准，本结果为可配置参考。")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="密评符合率计算与总体结论判定（规则以 GM/T 0116 为准，阈值可配置）",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        help="测评结果 JSON 文件路径（- 表示从标准输入读取）；缺省为交互模式",
    )
    parser.add_argument("--pass-rate", type=float, default=0.90, help="符合阈值（默认0.90）")
    parser.add_argument("--fail-rate", type=float, default=0.60, help="基本符合阈值（默认0.60）")
    parser.add_argument("--raw", action="store_true", help="输出原始 JSON（供程序使用）")
    args = parser.parse_args()

    if args.pass_rate < 0 or args.fail_rate < 0 or args.pass_rate < args.fail_rate:
        parser.error("阈值无效：需 0 <= fail-rate <= pass-rate <= 1")

    try:
        if args.json:
            if args.json == "-":
                text = sys.stdin.read()
            else:
                with open(args.json, "r", encoding="utf-8-sig") as f:
                    text = f.read()
            items = parse_items(text)
        else:
            items = interactive_input()

        if not items:
            print("没有输入任何测评项，退出。", file=sys.stderr)
            return 1

        res = compute(items, args.pass_rate, args.fail_rate)
        if "error" in res:
            print(f"错误: {res['error']}", file=sys.stderr)
            return 1

        if args.raw:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(format_report(res))
        return 0
    except (ValueError, json.JSONDecodeError) as e:
        print(f"输入错误: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
