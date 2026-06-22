package com.dayagent.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

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

    @SuppressWarnings("unchecked")
    public Map<String, Object> callChat(Map<String, Object> request) {
        // Chat 和 Plan 一样，都经由 Java 统一代理到 Python Agent。
        // 这样前端永远只面对 /api/*，鉴权和上下文收集都留在 Java 侧。
        String url = agentBaseUrl + "/chat";
        try {
            return restTemplate.postForObject(url, request, Map.class);
        } catch (Exception e) {
            // 对话失败时返回同形状降级结果，前端不用为异常响应写额外分支。
            return Map.of(
                    "reply", "AI 助手暂时不可用：" + e.getMessage(),
                    "used_context", List.of(),
                    "tool_results", List.of()
            );
        }
    }
}
