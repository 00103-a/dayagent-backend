package com.dayagent.service;

import com.dayagent.entity.Goal;
import com.dayagent.entity.DailySummary;
import com.dayagent.entity.DailyPlan;
import com.dayagent.entity.Parcel;
import com.dayagent.mapper.GoalMapper;
import com.dayagent.mapper.DailySummaryMapper;
import com.dayagent.mapper.DailyPlanMapper;
import com.dayagent.mapper.ParcelMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 调用 Python Agent 层获取规划
 */
@Service
@RequiredArgsConstructor
public class AgentCallerService {

    private final AgentHttpClient agentHttpClient;
    private final GoalMapper goalMapper;
    private final DailySummaryMapper dailySummaryMapper;
    private final DailyPlanMapper dailyPlanMapper;
    private final ParcelMapper parcelMapper;
    private final ObjectMapper objectMapper;

    /**
     * 查询今天已缓存的规划
     * @return 缓存的 PlanResponse，或 null 表示今天还没生成过
     */
    public PlanResponse getCachedPlan(Long userId) {
        DailyPlan cached = dailyPlanMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<DailyPlan>()
                        .eq(DailyPlan::getUserId, userId)
                        .eq(DailyPlan::getPlanDate, LocalDate.now())
                        .orderByDesc(DailyPlan::getCreatedAt)
                        .last("LIMIT 1")
        );
        if (cached == null) {
            return null;
        }
        PlanResponse response = new PlanResponse();
        response.setPlan(cached.getContent());
        // rawData 是 JSON，解析回 priorities/warnings
        if (cached.getRawData() != null) {
            try {
                PlanResponse extra = objectMapper.readValue(cached.getRawData(), PlanResponse.class);
                response.setPriorities(extra.getPriorities());
                response.setWarnings(extra.getWarnings());
                response.setParcels(extra.getParcels());
            } catch (JsonProcessingException e) {
                // rawData 解析失败则降级为空
            }
        }
        return response;
    }

    /**
     * 生成某用户的今日规划，并保存到 daily_plan 表
     */
    public PlanResponse generatePlan(Long userId, String location) {
        // 1. 查用户昨天的总结
        DailySummary yesterday = dailySummaryMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<DailySummary>()
                        .eq(DailySummary::getUserId, userId)
                        .orderByDesc(DailySummary::getSummaryDate)
                        .last("LIMIT 1")
        );

        // 2. 查活跃目标
        List<Goal> activeGoals = goalMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<Goal>()
                        .eq(Goal::getUserId, userId)
                        .eq(Goal::getStatus, "active")
        );

        // 3. 查未签收的快递
        List<Parcel> undeliveredParcels = parcelMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<Parcel>()
                        .eq(Parcel::getUserId, userId)
                        .eq(Parcel::getIsDelivered, false)
        );

        List<PlanRequest.ParcelInfo> parcelInfos = undeliveredParcels.stream()
                .map(p -> PlanRequest.ParcelInfo.builder()
                        .trackingNo(p.getTrackingNo())
                        .carrier(p.getCarrier())
                        .remark(p.getRemark())
                        .build())
                .toList();

        // 4. 组装请求发到 Python
        PlanRequest request = PlanRequest.builder()
                .userId(String.valueOf(userId))
                .yesterdaySummary(yesterday != null ? yesterday.getContent() : "")
                .goals(activeGoals.stream().map(Goal::getContent).toList())
                .location(location)
                .parcels(parcelInfos)
                .build();

        PlanResponse response = agentHttpClient.callGeneratePlan(request);

        // 5. 保存规划到 daily_plan 表，下次访问可直接取缓存
        savePlanToCache(userId, response);

        // 6. 根据 Python 返回的快递状态更新数据库
        if (response.getParcels() != null) {
            for (PlanResponse.ParcelStatus ps : response.getParcels()) {
                for (Parcel p : undeliveredParcels) {
                    if (p.getTrackingNo().equals(ps.getTrackingNo())) {
                        p.setStatus(ps.getState());
                        if (ps.getDetails() != null && !ps.getDetails().isEmpty()) {
                            try {
                                p.setTrackDetails(objectMapper.writeValueAsString(ps.getDetails()));
                            } catch (JsonProcessingException ignored) {
                            }
                        }
                        p.setLastChecked(LocalDateTime.now());
                        if (Boolean.TRUE.equals(ps.getIsDelivered())) {
                            p.setIsDelivered(true);
                        }
                        parcelMapper.updateById(p);
                        break;
                    }
                }
            }
        }

        return response;
    }

    /**
     * 将规划保存到 daily_plan 表（当下同一天已有记录则更新）
     */
    private void savePlanToCache(Long userId, PlanResponse response) {
        DailyPlan existing = dailyPlanMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<DailyPlan>()
                        .eq(DailyPlan::getUserId, userId)
                        .eq(DailyPlan::getPlanDate, LocalDate.now())
                        .last("LIMIT 1")
        );

        // 将 priorities/warnings/parcels 合并序列化到 rawData JSON
        String rawData = null;
        try {
            PlanResponse extras = new PlanResponse();
            extras.setPriorities(response.getPriorities());
            extras.setWarnings(response.getWarnings());
            extras.setParcels(response.getParcels());
            rawData = objectMapper.writeValueAsString(extras);
        } catch (JsonProcessingException ignored) {
        }

        if (existing != null) {
            existing.setContent(response.getPlan());
            existing.setRawData(rawData);
            dailyPlanMapper.updateById(existing);
        } else {
            DailyPlan dp = new DailyPlan();
            dp.setUserId(userId);
            dp.setPlanDate(LocalDate.now());
            dp.setContent(response.getPlan());
            dp.setRawData(rawData);
            dailyPlanMapper.insert(dp);
        }
    }
}
