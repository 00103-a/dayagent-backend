package com.dayagent.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 定时任务（每天早上 8 点自动生成规划并推送）
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ScheduleService {

    private final AgentCallerService agentCallerService;
    private final PushService pushService;

    /**
     * 每天早上 8:00 执行
     * cron 表达式：秒 分 时 日 月 周
     */
    @Scheduled(cron = "0 0 8 * * ?")
    public void morningPlanGeneration() {
        log.info("开始执行每日早8点规划任务...");
        // TODO: 遍历所有活跃用户，逐个生成规划并推送
        // 暂用占位
        log.info("每日规划任务执行完毕");
    }
}
