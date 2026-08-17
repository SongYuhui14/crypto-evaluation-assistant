#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_checklist.py — 按等级 + 行业生成密评检查清单（Markdown）

用途：
    密评检测前，根据被测系统的等级保护级别（二级/三级/四级）与行业
    （通用/金融/政务/能源），生成对应的检查清单，供现场逐项核对。

用法：
    python gen_checklist.py --level 3 --industry finance
    python gen_checklist.py --level 2                 # 默认通用行业
    python gen_checklist.py --list                    # 列出可选行业

说明：
    - 清单内容来自 references/checklist*.md（知识库），脚本负责组装与分级，
      保证"知识在文档、逻辑在脚本"。
    - 测评项编号、权重、判定阈值一律以 GB/T 39786-2021、GM/T 0115-2021、
      GM/T 0116-2021 官方文本为准，本脚本不生成测评项编号。
"""

import argparse
import io
import os
import sys

# Windows 控制台默认 GBK，强制 stdout/stderr 使用 UTF-8 以支持 ⚠️ 等符号
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 脚本所在目录（scripts/），技能根目录在其上一级
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
REFERENCES_DIR = os.path.join(SKILL_ROOT, "references")

# 行业 -> 清单文件名映射（references/checklist/ 下）
INDUSTRY_FILES = {
    "finance": "finance.md",
    "government": "government.md",
    "energy": "energy.md",
}

# 各等级通用说明（骨架来自 SKILL.md / standards-map.md 的框架认知）
LEVEL_NOTES = {
    "2": "二级系统：测评范围为基础要求，重点关注身份鉴别、传输与存储保护的密码应用。",
    "3": "三级系统：在二级基础上扩展，需关注完整的技术要求与管理要求，测评项更多、取证要求更严。",
    "4": "四级系统：最高等级要求，密码应用强度与测评严格度最高，通常涉及关键信息基础设施。",
}


def read_text(path):
    """读取 UTF-8 文本，容错 BOM。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def build_generic_checklist():
    """从 references/checklist.md 读取通用清单。"""
    path = os.path.join(REFERENCES_DIR, "checklist.md")
    if not os.path.exists(path):
        return None, f"未找到通用清单: {path}"
    return read_text(path), None


def build_industry_checklist(industry):
    """读取行业清单正文（去掉其开头的说明头，避免重复）。"""
    fname = INDUSTRY_FILES.get(industry)
    if not fname:
        return None, f"未知行业: {industry}（可选: {', '.join(sorted(INDUSTRY_FILES))}）"
    path = os.path.join(REFERENCES_DIR, "checklist", fname)
    if not os.path.exists(path):
        return None, f"未找到行业清单: {path}"
    return read_text(path), None


def generate(level, industry):
    """组装一份检查清单 Markdown。"""
    level_key = str(level)
    if level_key not in LEVEL_NOTES:
        return None, f"无效等级: {level}（可选: 2/3/4）"

    lines = []
    lines.append(f"# 密评检测检查清单（等级{level_key} · {industry}行业）")
    lines.append("")
    lines.append(f"> 由 crypto-evaluation-assistant 的 gen_checklist.py 生成。")
    lines.append("> ⚠️ 测评项编号、权重、判定阈值以 GB/T 39786-2021、GM/T 0115-2021、")
    lines.append("> GM/T 0116-2021 官方文本为准；本清单为工作框架，现场以实测证据为准。")
    lines.append("")
    lines.append(f"**等级说明**：{LEVEL_NOTES[level_key]}")
    lines.append("")
    lines.append("判定符号：✅ 符合 ｜ ◐ 部分符合 ｜ ❌ 不符合 ｜ ➖ 不适用")
    lines.append("")

    if industry == "generic":
        body, err = build_generic_checklist()
        if err:
            return None, err
        lines.append(body)
    else:
        body, err = build_industry_checklist(industry)
        if err:
            return None, err
        # 行业清单自带行业特点说明，直接附上
        lines.append(body)
        # 补充通用清单作为基础参照（行业清单聚焦行业特有项）
        generic, gerr = build_generic_checklist()
        if not gerr:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("## 通用基础清单（行业清单未覆盖的通用项）")
            lines.append("")
            lines.append(generic)

    return "\n".join(lines), None


def main():
    parser = argparse.ArgumentParser(
        description="生成密评检查清单（按等级+行业）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python gen_checklist.py --level 3 --industry finance\n"
               "  python gen_checklist.py --level 2\n"
               "  python gen_checklist.py --list",
    )
    parser.add_argument("--level", type=int, choices=[2, 3, 4], help="等级保护级别（2/3/4）")
    parser.add_argument(
        "--industry",
        default="generic",
        help="行业: generic(默认)/finance/government/energy",
    )
    parser.add_argument("--list", action="store_true", help="列出可选行业并退出")
    parser.add_argument(
        "-o", "--output", help="输出文件路径（默认输出到 stdout）"
    )
    args = parser.parse_args()

    if args.list:
        print("可选行业:")
        print("  generic    - 通用（所有行业基础）")
        for k in sorted(INDUSTRY_FILES):
            print(f"  {k:<11} - {INDUSTRY_FILES[k]}")
        return 0

    if args.level is None:
        parser.error("必须指定 --level（或使用 --list）")

    content, err = generate(args.level, args.industry)
    if err:
        print(f"错误: {err}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"已生成: {args.output}")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
