from agent_service.workflows.chat import build_personal_context_text, fallback_need_analysis


def main():
    context = {
        "today_plan": "上午复习信号系统，下午整理 DayAgent。",
        "active_goals": [
            {"type": "weekly", "content": "完成 Python agent-service 梳理"},
        ],
        "recent_summaries": [
            {"summaryDate": "2026-06-20", "content": "今天推进了工具抽象。", "moodScore": 4},
        ],
        "profile": {"default_location": "南昌"},
    }

    text, used = build_personal_context_text(context, "近 7 天精力稳定")

    assert "今日规划" in text
    assert "活跃目标" in text
    assert "最近总结" in text
    assert "长期记忆分析" in text
    assert "今日规划" in used
    assert "长期记忆分析" in used

    analysis = fallback_need_analysis("我今天很累，但还想推进目标，应该怎么安排？", context)
    assert analysis["need_type"] in {"emotion", "planning", "goal"}
    assert "今日规划" in analysis["personal_factors"]

    weather_analysis = fallback_need_analysis("今天会下雨吗，要不要带伞？", context)
    assert "weather" in weather_analysis["should_use_tools"]

    print("chat workflow shape ok")


if __name__ == "__main__":
    main()
