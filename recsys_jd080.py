"""recsys_jd080 —— 在推荐系统算法工程师·多轮工具链的失败定位里找出重复内容并给出归并建议。

对内容做归一化与分片比对，找出推荐系统算法工程师·多轮工具链的失败定位上的重复项并按相似度归并

定位：
  按归一化后的分片相似度判断，而不是按字符串完全相等

岗位对应：
  目标岗位　Mistral AI · 中级推荐系统算法工程师
  技能主线　推荐系统、特征工程、Python
  领域标签　搜索推荐广告

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python recsys_jd080.py --help
    python recsys_jd080.py --file input.txt
    python recsys_jd080.py --text "示例内容"
    python recsys_jd080.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：Mistral AI · 中级推荐系统算法工程师
RULES: list[dict] = [
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·缺失",
        "why": "岗位要求「推荐系统」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', '推荐系统'],
    },
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·冲突",
        "why": "两处关于「特征工程」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', '特征工程'],
    },
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·越界",
        "why": "「Python」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', 'Python'],
    },
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·退化",
        "why": "「搜索推荐广告」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', '搜索推荐广告'],
    },
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·泄漏",
        "why": "「推荐系统算法工程师」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', '推荐系统算法工程师'],
    },
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·重复#2",
        "why": "同一处「推荐系统」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', '推荐系统'],
    },
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·陈旧#2",
        "why": "「特征工程」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', '特征工程'],
    },
    {
        "name": "推荐系统算法工程师·多轮工具链的失败定位·不可核#2",
        "why": "关于「Python」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', 'Python'],
    },
]


def recsys_jd080_normalize(text: str) -> str:
    """归一化：去空白、转小写、去标点。"""
    t = re.sub(r"\s+", "", text.lower())
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", t)


def recsys_jd080_shingles(text: str, k: int = 3) -> set[str]:
    """字符 k-gram 集合。"""
    n = recsys_jd080_normalize(text)
    if len(n) <= k:
        return {n} if n else set()
    return {n[i:i + k] for i in range(len(n) - k + 1)}


def recsys_jd080_jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def recsys_jd080_group(items: list[str], threshold: float = 0.6) -> list[list[int]]:
    """按相似度做贪心聚类，返回每组的下标列表。"""
    sigs = [recsys_jd080_shingles(x) for x in items]
    groups: list[list[int]] = []
    assigned = [False] * len(items)
    for i in range(len(items)):
        if assigned[i]:
            continue
        recsys_jd080_group = [i]
        assigned[i] = True
        for j in range(i + 1, len(items)):
            if assigned[j]:
                continue
            if recsys_jd080_jaccard(sigs[i], sigs[j]) >= threshold:
                recsys_jd080_group.append(j)
                assigned[j] = True
        groups.append(recsys_jd080_group)
    return groups


def recsys_jd080_analyze(text: str) -> dict:
    """主分析：单文本内的重复段落与近似重复。"""
    blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    groups = recsys_jd080_group(blocks)
    dup_groups = [g for g in groups if len(g) > 1]
    exact = []
    seen: dict[str, list[int]] = {}
    for i, b in enumerate(blocks):
        key = recsys_jd080_normalize(b)
        if key in seen:
            exact.append({"first": seen[key][0], "dup": i})
        else:
            seen.setdefault(key, []).append(i)
    return {
        "block_count": len(blocks),
        "groups": len(groups),
        "duplicate_groups": dup_groups,
        "exact_duplicates": exact,
        "redundancy": round(sum(len(g) - 1 for g in dup_groups) / len(blocks), 4) if blocks else 0.0,
        "clean": not dup_groups and not exact,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"段落数：{result['block_count']}  聚类：{result['groups']}")
    out.append(f"冗余率：{result['redundancy']:.2%}")
    out.append("")
    for g in result["duplicate_groups"]:
        out.append(f"重复组（{len(g)} 份）：{g}")
    if result["clean"]:
        out.append("没有发现重复。")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="recsys_jd080",
        description="对内容做归一化与分片比对，找出推荐系统算法工程师·多轮工具链的失败定位上的重复项并按相似度归并（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python recsys_jd080.py --file input.txt\n"
            "  python recsys_jd080.py --text '示例内容'\n"
            "  python recsys_jd080.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = recsys_jd080_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
