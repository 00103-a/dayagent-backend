package com.dayagent.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;

/**
 * 封装对 Python Agent 服务的 HTTP 调用
 */
@Service
@RequiredArgsConstructor
public class AgentHttpClient {

    private final RestTemplate restTemplate;

    @Value("${agent.base-url}")
    private String agentBaseUrl;

    /**
     * 调用 POST /generate-plan，失败返回降级数据
     */
    public PlanResponse callGeneratePlan(PlanRequest request) {
        String url = agentBaseUrl + "/generate-plan";
        try {
            return restTemplate.postForObject(url, request, PlanResponse.class);
        } catch (Exception e) {
            // 降级：Python 挂了不阻塞主流程，返回备用提示
            PlanResponse fallback = new PlanResponse();
            fallback.setPlan("今日规划暂时无法生成，请稍后重试。\n建议：先完成昨日未做完的任务。");
            fallback.setPriorities(List.of());
            fallback.setWarnings(List.of("Agent 服务不可用：" + e.getMessage()));
            return fallback;
        }
    }
}
