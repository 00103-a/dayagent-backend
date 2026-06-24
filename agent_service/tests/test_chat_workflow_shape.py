from agent_service.workflows.chat import build_personal_context_text, fallback_need_analysis


def main():
    # 这个测试不调用真实 LLM，也不连数据库。
    # 它只保证 Chat workflow 的关键“形状”稳定：
    # 1. 个人上下文会被整理进 prompt；
    # 2. LLM 不可用时的兜底需求分析还能选出大致类型和工具。
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

    # used 是给前端展示的可解释来源列表，不是模型内部推理链。
    assert "今日规划" in text
    assert "活跃目标" in text
    assert "最近总结" in text
    assert "长期记忆分析" in text
    assert "今日规划" in used
    assert "长期记忆分析" in used

    analysis = fallback_need_analysis("我今天很累，但还想推进目标，应该怎么安排？", context)
    # “累 + 推进目标 + 怎么安排”可能落到情绪/规划/目标任一类；
    # 这里不压死分类细节，只要求它能识别为非泛聊。
    assert analysis["need_type"] in {"emotion", "planning", "goal"}
    assert "今日规划" in analysis["personal_factors"]

    weather_analysis = fallback_need_analysis("今天会下雨吗，要不要带伞？", context)
    # 天气关键词应该触发 weather 工具选择。
    assert "weather" in weather_analysis["should_use_tools"]

    print("chat workflow shape ok")


if __name__ == "__main__":
    main()
