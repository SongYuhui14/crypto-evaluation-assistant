#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_report.py — 从测评结果生成密评报告初稿（Markdown）

用途：
    输入被测系统信息 + 各测评项判定结果，生成一份可直接编辑的测评报告初稿
    （含项目概况、测评范围、逐项结果、符合率汇总、总体结论、整改建议）。

输入（JSON 文件 / 标准输入，结构如下）：
{
  "project": {
    "name": "XX银行核心业务系统密评项目",
    "unit": "XX银行",
    "agency": "XX测评机构",
    "date": "2026-03-01",
    "report_no": "MP-2026-001",
    "level": "三级",
    "scope": "核心业务系统及其网络边界、密钥管理、安全管理",
    "devices": "金融数据密码机×2、签名验签服务器×2、USBKey 若干"
  },
  "items": [
    {"layer": "物理和环境安全", "item": "门禁身份鉴别", "result": "符合", "weight": 10, "evidence": "门禁系统使用国密SM2认证卡片，配置截图 #A-01"},
    {"layer": "网络和通信安全", "item": "传输机密性", "result": "部分符合", "weight": 15, "evidence": "部分链路仍使用TLS1.2国际套件，抓包记录 #B-03"},
    {"layer": "密钥管理", "item": "密钥存储", "result": "不符合", "weight": 20, "evidence": "发现配置文件明文密钥，扫描报告 #E-07"}
  ],
  "fixes": [
    {"priority": "高", "layer": "密钥管理", "issue": "密钥明文存储", "action": "密钥迁入密码机/KMS并立即轮换", "owner": "系统部"},
    {"priority": "中", "layer": "网络和通信安全", "issue": "未使用国密套件", "action": "配置国密TLCP套件并复测", "owner": "网络部"}
  ]
}

用法：
    python gen_report.py --json input.json -o report.md
    python gen_report.py --json input.json            # 输出到 stdout
    echo '{...}' | python gen_report.py --json - -o report.md

说明：
    - 计分逻辑与 calc_conformance.py 一致（部分符合×0.5、不适用剔除分母、阈值可配）
    - 输出为报告**初稿**：测评项编号、权重、阈值及结论须人工对照
      GB/T 39786-2021、GM/T 0115/0116-2021 官方文本核实后再定稿
"""

import argparse
import datetime
import io
import json
import os
import sys

# Windows 控制台默认 GBK，强制 UTF-8 输出以支持符号
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VALID_RESULTS = {"符合", "部分符合", "不符合", "不适用"}
LAYERS = ["物理和环境安全", "网络和通信安全", "设备和计算安全",
          "应用和数据安全", "密钥管理", "安全管理"]
RESULT_SYMBOL = {"符合": "✅", "部分符合": "◐", "不符合": "❌", "不适用": "➖"}


def parse_input(text):
    """解析 JSON 输入。"""
    data = json.loads(text)
    if not isinstance(data, dict) or "items" not in data:
        raise ValueError("JSON 必须是对象且包含 items 数组")
    project = data.get("project", {})
    items = data["items"]
    fixes = data.get("fixes", [])
    if not isinstance(items, list):
        raise ValueError("items 必须是数组")

    parsed = []
    for i, entry in enumerate(items):
        if not isinstance(entry, dict):
            raise ValueError(f"第 {i+1} 个测评项不是对象")
        result = entry.get("result")
        if result not in VALID_RESULTS:
            raise ValueError(
                f"测评项 '{entry.get('item', i+1)}' 的 result 无效: {result!r}"
            )
        weight = float(entry.get("weight", 10))
        if weight <= 0:
            raise ValueError(f"测评项 '{entry.get('item')}' 的 weight 必须为正数")
        parsed.append({
            "layer": entry.get("layer", "未分类"),
            "item": entry.get("item", f"测评项{i+1}"),
            "result": result,
            "weight": weight,
            "evidence": entry.get("evidence", ""),
        })
    return project, parsed, fixes


def compute(items, pass_rate, fail_rate):
    """与 calc_conformance.py 一致的计分逻辑。"""
    total_weight = 0.0
    earned = 0.0
    counts = {"符合": 0, "部分符合": 0, "不符合": 0, "不适用": 0}
    for it in items:
        counts[it["result"]] += 1
        if it["result"] == "不适用":
            continue
        total_weight += it["weight"]
        if it["result"] == "符合":
            earned += it["weight"]
        elif it["result"] == "部分符合":
            earned += it["weight"] * 0.5

    if total_weight <= 0:
        return None
    conformance = earned / total_weight
    if conformance >= pass_rate:
        conclusion = "符合"
    elif conformance >= fail_rate:
        conclusion = "基本符合"
    else:
        conclusion = "不符合"
    return {
        "counts": counts,
        "effective_weight": total_weight,
        "earned_weight": earned,
        "conformance": round(conformance, 4),
        "conformance_percent": round(conformance * 100, 2),
        "conclusion": conclusion,
    }


def esc(text):
    """表格单元格转义（去掉竖线）。"""
    return str(text).replace("|", "／").replace("\n", " ")


def gen_report(project, items, fixes, pass_rate, fail_rate):
    """生成报告 Markdown。"""
    res = compute(items, pass_rate, fail_rate)
    L = []
    L.append("# 商用密码应用安全性评估报告（初稿）")
    L.append("")
    L.append("> 本报告由 crypto-evaluation-assistant 的 gen_report.py 自动生成初稿。")
    L.append("> ⚠️ 测评项编号、权重、符合率阈值与总体结论以 GB/T 39786-2021、")
    L.append("> GM/T 0115-2021、GM/T 0116-2021 官方文本为准；人工核实后再定稿。")
    L.append("")
    L.append("## 1. 项目概况")
    L.append("")
    L.append("| 项目 | 内容 |")
    L.append("|---|---|")
    L.append(f"| 项目名称 | {esc(project.get('name', '<待填写>'))} |")
    L.append(f"| 被评估单位 | {esc(project.get('unit', '<待填写>'))} |")
    L.append(f"| 测评机构 | {esc(project.get('agency', '<待填写>'))} |")
    L.append(f"| 测评日期 | {esc(project.get('date', datetime.date.today().isoformat()))} |")
    L.append(f"| 报告编号 | {esc(project.get('report_no', '<待填写>'))} |")
    L.append("| 测评依据 | GB/T 39786-2021；GM/T 0115-2021；GM/T 0116-2021 |")
    L.append("")
    L.append("## 2. 测评对象与范围")
    L.append("")
    L.append(f"- 等级保护级别：{esc(project.get('level', '<二级/三级/四级>'))}")
    L.append(f"- 系统边界与范围：{esc(project.get('scope', '<待填写>'))}")
    L.append(f"- 密码产品与设备清单：{esc(project.get('devices', '<待填写>'))}")
    L.append("")
    L.append("## 3. 单项测评结果")
    L.append("")
    L.append("判定符号：✅ 符合 ｜ ◐ 部分符合 ｜ ❌ 不符合 ｜ ➖ 不适用")
    L.append("")
    L.append("| 层面 | 测评项 | 判定 | 权重 | 证据/说明 |")
    L.append("|---|---|---|---|---|")
    for it in items:
        L.append(
            f"| {esc(it['layer'])} | {esc(it['item'])} | "
            f"{RESULT_SYMBOL[it['result']]} {it['result']} | "
            f"{it['weight']:.0f} | {esc(it['evidence'])} |"
        )
    L.append("")
    L.append("## 4. 总体评价与结论")
    L.append("")
    if res:
        c = res["counts"]
        L.append(f"- 测评项统计：符合 {c['符合']} 项 / 部分符合 {c['部分符合']} 项 "
                 f"/ 不符合 {c['不符合']} 项 / 不适用 {c['不适用']} 项")
        L.append(f"- 参与计分权重：{res['effective_weight']:.0f}（不适用项不计入）")
        L.append(f"- 实得权重：{res['earned_weight']:.2f}（部分符合按 0.5 折算）")
        L.append(f"- 符合率：**{res['conformance_percent']:.2f}%**")
        L.append(f"- 总体结论：**{res['conclusion']}**")
        if c["不符合"] > 0:
            L.append("")
            L.append("> ⚠️ 存在不符合项，请人工核查是否含红线问题（默认口令、明文密钥、")
            L.append("> 无认证密码产品等）；红线项可能直接否决总体结论。")
    else:
        L.append("- 无有效计分测评项（全部不适用或无数据），无法计算符合率。")
    L.append("")
    L.append("## 5. 整改建议")
    L.append("")
    if fixes:
        L.append("| 优先级 | 层面 | 问题 | 整改措施 | 建议责任方 |")
        L.append("|---|---|---|---|---|")
        for f in fixes:
            L.append(
                f"| {esc(f.get('priority', '中'))} | {esc(f.get('layer', ''))} | "
                f"{esc(f.get('issue', ''))} | {esc(f.get('action', ''))} | "
                f"{esc(f.get('owner', ''))} |"
            )
    else:
        L.append("（未提供整改建议，请人工补充——按'先说最危险、最影响结论的项'排序。）")
    L.append("")
    L.append("## 6. 附录")
    L.append("")
    L.append("- 附录 A：被测系统拓扑图")
    L.append("- 附录 B：检测工具与记录")
    L.append("- 附录 C：访谈记录")
    L.append("- 附录 D：证书与产品认证材料清单")
    L.append("")
    L.append("---")
    L.append("")
    L.append("> 撰写要点：证据与结论一致、不空口断言、量化结论、前后数字一致、整改可落地、")
    L.append("> 保密与合规。详细模板见 references/report-template.md。")
    return "\n".join(L)


def main():
    parser = argparse.ArgumentParser(
        description="从测评结果生成密评报告初稿（Markdown）",
    )
    parser.add_argument("--json", metavar="PATH", required=True,
                        help="输入 JSON 路径（- 表示标准输入）")
    parser.add_argument("-o", "--output", help="输出 Markdown 路径（默认 stdout）")
    parser.add_argument("--pass-rate", type=float, default=0.90)
    parser.add_argument("--fail-rate", type=float, default=0.60)
    args = parser.parse_args()

    if args.pass_rate < args.fail_rate:
        parser.error("阈值无效：fail-rate 不能大于 pass-rate")

    try:
        if args.json == "-":
            text = sys.stdin.read()
        else:
            with open(args.json, "r", encoding="utf-8-sig") as f:
                text = f.read()
        project, items, fixes = parse_input(text)
        if not items:
            print("items 为空，无法生成报告。", file=sys.stderr)
            return 1
        md = gen_report(project, items, fixes, args.pass_rate, args.fail_rate)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"已生成报告初稿: {args.output}")
        else:
            print(md)
        return 0
    except (ValueError, json.JSONDecodeError) as e:
        print(f"输入错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
