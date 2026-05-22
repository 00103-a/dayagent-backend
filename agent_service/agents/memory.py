"""长期记忆分析：精力趋势、未完成事项检测、目标进度检查"""
import asyncio
from datetime import date, datetime

from agent_service.tools.mysql_client import fetch_all


async def _energy_trend(user_id: str) -> str:
    """查询近 7 天精力评分，分析趋势"""
    rows = await fetch_all(
        """SELECT summary_date, mood_score
           FROM daily_summary
           WHERE user_id = %s
             AND summary_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
             AND mood_score IS NOT NULL
           ORDER BY summary_date ASC""",
        (int(user_id),),
    )
    if not rows:
        return "暂无精力数据（近 7 天总结未记录 mood_score）"

    scores = [r["mood_score"] for r in rows]
    avg = sum(scores) / len(scores)
    latest = rows[-1]

    # 趋势：比较前3天vs后3天均值
    mid = len(scores) // 2
    first_half_avg = sum(scores[:mid]) / mid if mid > 0 else scores[0]
    second_half_avg = sum(scores[mid:]) / (len(scores) - mid) if len(scores) - mid > 0 else scores[-1]
    if second_half_avg > first_half_avg + 0.5:
        trend_text = "上升中 ↑"
    elif second_half_avg < first_half_avg - 0.5:
        trend_text = "下降中 ↓"
    else:
        trend_text = "持平 →"

    # 连续低精力检测（≤2）
    max_low_streak = 0
    cur_streak = 0
    for s in scores:
        if s <= 2:
            cur_streak += 1
            max_low_streak = max(max_low_streak, cur_streak)
        else:
            cur_streak = 0

    lines = [
        f"近 {len(scores)} 天精力均值 {avg:.1f}/5，趋势{trend_text}",
        f"最近一次：{latest['summary_date']} → {latest['mood_score']}/5",
    ]
    if max_low_streak >= 2:
        lines.append(f"⚠ 连续 {max_low_streak} 天精力偏低（≤2），今日建议减轻任务量")
    elif avg >= 4.0:
        lines.append("✅ 近期精力充沛，可以安排高难度任务")

    return "【精力趋势】\n" + "\n".join(lines)


async def _plan_summary_contrast(user_id: str) -> str:
    """查近 7 天规划与总结原始数据，供上层 LLM 分析未完成事项"""
    plan_rows = await fetch_all(
        """SELECT plan_date, content
           FROM daily_plan
           WHERE user_id = %s
             AND plan_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
           ORDER BY plan_date ASC""",
        (int(user_id),),
    )
    summary_rows = await fetch_all(
        """SELECT summary_date, content
           FROM daily_summary
           WHERE user_id = %s
             AND summary_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
           ORDER BY summary_date ASC""",
        (int(user_id),),
    )

    if not plan_rows and not summary_rows:
        return "暂无规划/总结数据（近 7 天无记录）"

    # 按日期配对
    plan_map = {r["plan_date"].isoformat(): r["content"] for r in plan_rows}
    summary_map = {r["summary_date"].isoformat(): r["content"] for r in summary_rows}
    all_dates = sorted(set(plan_map.keys()) | set(summary_map.keys()))

    pairs = []
    for d in all_dates:
        plan = plan_map.get(d, "(无规划)")
        summary = summary_map.get(d, "(无总结)")
        # 截断过长文本
        plan_short = plan[:200] + "..." if len(plan) > 200 else plan
        summary_short = summary[:200] + "..." if len(summary) > 200 else summary
        pairs.append(f"- {d}\n  规划：{plan_short}\n  总结：{summary_short}")

    return "【近期规划 vs 总结对比】\n" + "\n".join(pairs)


async def _goal_progress(user_id: str) -> str:
    """检查活跃目标推进情况"""
    rows = await fetch_all(
        """SELECT type, content, start_date, end_date, status
           FROM goal
           WHERE user_id = %s AND status = 'active'
           ORDER BY FIELD(type, 'weekly', 'monthly'), start_date ASC""",
        (int(user_id),),
    )
    if not rows:
        return ""

    today = date.today()
    goal_lines = []
    for g in rows:
        start = g["start_date"]
        end = g["end_date"]
        elapsed = (today - start).days if start else None
        total = (end - start).days if start and end else None

        if elapsed is not None and total is not None and total > 0:
            pct = min(100, int(elapsed / total * 100))
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            progress = f"[{bar}] {pct}%"
            if pct >= 80:
                warning = " ⚠ 即将到期"
            elif pct >= 100:
                warning = " 🔴 已超期"
            else:
                warning = ""
            goal_lines.append(f"- [{g['type']}] {g['content']}  {progress}{warning}")
        else:
            goal_lines.append(f"- [{g['type']}] {g['content']}（时间未设定）")

    return "【活跃目标进度】\n" + "\n".join(goal_lines)


async def analyze_history(user_id: str) -> str:
    """分析用户近 30 天总结，找出规律和习惯

    并行执行三项分析：精力趋势、规划总结对比、目标进度
    """
    energy, contrast, goals = await asyncio.gather(
        _energy_trend(user_id),
        _plan_summary_contrast(user_id),
        _goal_progress(user_id),
    )

    parts = [p for p in [energy, contrast, goals] if p]
    if not parts:
        return "数据不足，暂无长期记忆分析"

    return "\n\n".join(parts)
