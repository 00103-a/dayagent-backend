package com.dayagent.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.dayagent.entity.DailyPlan;
import com.dayagent.entity.DailySummary;
import com.dayagent.entity.Goal;
import com.dayagent.entity.Parcel;
import com.dayagent.entity.UserSettings;
import com.dayagent.mapper.DailyPlanMapper;
import com.dayagent.mapper.DailySummaryMapper;
import com.dayagent.mapper.GoalMapper;
import com.dayagent.mapper.ParcelMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ChatService {

    private final AgentHttpClient agentHttpClient;
    private final UserSettingsService userSettingsService;
    private final DailyPlanMapper dailyPlanMapper;
    private final DailySummaryMapper dailySummaryMapper;
    private final GoalMapper goalMapper;
    private final ParcelMapper parcelMapper;

    public Map<String, Object> chat(Long userId, Map<String, Object> body) {
        // 只接受 message 作为用户输入；个人上下文由后端自己查，避免前端伪造。
        Object rawMessage = body.get("message");
        String message = rawMessage == null ? "" : String.valueOf(rawMessage).trim();
        if (message.isEmpty()) {
            return Map.of("reply", "你想聊什么？");
        }

        UserSettings settings = userSettingsService.getByUserId(userId);

        // 发给 Python 的请求分成三块：
        // 1. message：用户这次问什么；
        // 2. user_settings：LLM/API 配置；
        // 3. user_context：后端查到的可信个人上下文。
        Map<String, Object> request = new HashMap<>();
        request.put("userId", String.valueOf(userId));
        request.put("message", message);
        // client_context 只做补充信息保留，Python 当前会优先使用 user_context。
        request.put("client_context", body.getOrDefault("context", Map.of()));
        request.put("user_settings", userSettingsService.buildSettingsMap(settings));
        request.put("user_context", buildUserContext(userId, settings));
        return agentHttpClient.callChat(request);
    }

    private Map<String, Object> buildUserContext(Long userId, UserSettings settings) {
        // 这里是 Chat “了解用户”的来源。它不生成自然语言，只组装结构化数据；
        // Python workflow 再把这些数据转成 prompt，并决定哪些内容值得参考。
        Map<String, Object> context = new HashMap<>();
        context.put("profile", Map.of(
                "default_location", nullToEmpty(settings.getDefaultLocation())
        ));
        context.put("today_plan", findTodayPlan(userId));
        context.put("active_goals", findActiveGoals(userId));
        context.put("recent_summaries", findRecentSummaries(userId));
        context.put("active_parcels", findActiveParcels(userId));
        return context;
    }

    private String findTodayPlan(Long userId) {
        // 今日规划是对话最重要的上下文之一：用户问“现在做什么”时，Agent 应优先参考它。
        DailyPlan plan = dailyPlanMapper.selectOne(
                new LambdaQueryWrapper<DailyPlan>()
                        .eq(DailyPlan::getUserId, userId)
                        .eq(DailyPlan::getPlanDate, LocalDate.now())
                        .orderByDesc(DailyPlan::getCreatedAt)
                        .last("LIMIT 1")
        );
        return plan != null ? nullToEmpty(plan.getContent()) : "";
    }

    private List<Map<String, Object>> findActiveGoals(Long userId) {
        // 只取 active 目标，避免已完成目标干扰当前建议；按截止时间排序，越近越优先。
        List<Goal> goals = goalMapper.selectList(
                new LambdaQueryWrapper<Goal>()
                        .eq(Goal::getUserId, userId)
                        .eq(Goal::getStatus, "active")
                        .orderByAsc(Goal::getEndDate)
        );
        return goals.stream()
                .limit(8)
                .map(goal -> {
                    Map<String, Object> item = new HashMap<>();
                    item.put("type", nullToEmpty(goal.getType()));
                    item.put("content", nullToEmpty(goal.getContent()));
                    item.put("startDate", goal.getStartDate());
                    item.put("endDate", goal.getEndDate());
                    item.put("status", nullToEmpty(goal.getStatus()));
                    return item;
                })
                .toList();
    }

    private List<Map<String, Object>> findRecentSummaries(Long userId) {
        // 最近总结用于判断用户状态、精力和反复出现的问题；限制 5 条避免 prompt 过长。
        List<DailySummary> summaries = dailySummaryMapper.selectList(
                new LambdaQueryWrapper<DailySummary>()
                        .eq(DailySummary::getUserId, userId)
                        .orderByDesc(DailySummary::getSummaryDate)
                        .last("LIMIT 5")
        );
        return summaries.stream()
                .map(summary -> {
                    Map<String, Object> item = new HashMap<>();
                    item.put("summaryDate", summary.getSummaryDate());
                    item.put("content", nullToEmpty(summary.getContent()));
                    item.put("moodScore", summary.getMoodScore());
                    return item;
                })
                .toList();
    }

    private List<Map<String, Object>> findActiveParcels(Long userId) {
        // 快递不是每次都用，但当用户问取件/物流时，Python 可以选择 parcel 工具刷新状态。
        List<Parcel> parcels = parcelMapper.selectList(
                new LambdaQueryWrapper<Parcel>()
                        .eq(Parcel::getUserId, userId)
                        .eq(Parcel::getIsDelivered, false)
                        .orderByDesc(Parcel::getCreatedAt)
                        .last("LIMIT 8")
        );
        return parcels.stream()
                .map(parcel -> {
                    Map<String, Object> item = new HashMap<>();
                    item.put("tracking_no", nullToEmpty(parcel.getTrackingNo()));
                    item.put("carrier", nullToEmpty(parcel.getCarrier()));
                    item.put("remark", nullToEmpty(parcel.getRemark()));
                    item.put("status", nullToEmpty(parcel.getStatus()));
                    return item;
                })
                .toList();
    }

    private String nullToEmpty(String value) {
        return value == null ? "" : value;
    }
}
