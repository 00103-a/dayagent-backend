package com.dayagent.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

/**
 * 封装生活模块（天气/新闻/课表/学习通）对 Python Agent 的 HTTP 调用
 */
@Service
@RequiredArgsConstructor
public class LifeAgentClient {

    private final RestTemplate restTemplate;

    @Value("${agent.base-url}")
    private String agentBaseUrl;

    @SuppressWarnings("unchecked")
    public Map<String, Object> callWeather(String location, Double lat, Double lng) {
        StringBuilder url = new StringBuilder(agentBaseUrl + "/weather?location=" + location);
        if (lat != null && lng != null) {
            url.append("&lat=").append(lat).append("&lng=").append(lng);
        }
        try {
            Map<String, Object> resp = restTemplate.getForObject(url.toString(), Map.class);
            if (resp != null) {
                return Map.of(
                    "location", location,
                    "weather", resp.getOrDefault("weather", "天气数据获取失败"),
                    "condition_text", resp.getOrDefault("condition_text", ""),
                    "condition_icon", resp.getOrDefault("condition_icon", "")
                );
            }
            return Map.of("location", location, "weather", "天气数据获取失败",
                    "condition_text", "", "condition_icon", "");
        } catch (Exception e) {
            return Map.of("location", location, "weather", "天气服务暂不可用：" + e.getMessage(),
                    "condition_text", "", "condition_icon", "");
        }
    }

    public String callNews(String goals, String yesterdaySummary) {
        String url = agentBaseUrl + "/news?goals=" + goals + "&yesterday_summary=" + yesterdaySummary;
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restTemplate.getForObject(url, Map.class);
            return resp != null ? (String) resp.getOrDefault("news_text", "新闻数据获取失败") : "新闻数据获取失败";
        } catch (Exception e) {
            return "新闻服务暂不可用：" + e.getMessage();
        }
    }

    public String callChaoxingTasks() {
        String url = agentBaseUrl + "/chaoxing/tasks";
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restTemplate.getForObject(url, Map.class);
            return resp != null ? (String) resp.getOrDefault("tasks_text", "学习通数据获取失败") : "学习通数据获取失败";
        } catch (Exception e) {
            return "学习通服务暂不可用：" + e.getMessage();
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callListCourses(String week) {
        String url = agentBaseUrl + "/courses";
        if (week != null && !week.isBlank()) {
            url += "?week=" + week;
        }
        try {
            return restTemplate.getForObject(url, Map.class);
        } catch (Exception e) {
            return Map.of("count", 0, "courses", java.util.List.of(), "text", "课表服务暂不可用");
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callImportCourses() {
        String url = agentBaseUrl + "/courses/browser-import";
        try {
            return restTemplate.postForObject(url, null, Map.class);
        } catch (Exception e) {
            return Map.of("status", "error", "message", "导入失败：" + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callJsonImportCourses(Map<String, Object> body) {
        String url = agentBaseUrl + "/courses/import";
        try {
            return restTemplate.postForObject(url, body, Map.class);
        } catch (Exception e) {
            return Map.of("status", "error", "message", "导入失败：" + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callAiImportCourses(Map<String, Object> body) {
        String url = agentBaseUrl + "/courses/ai-import";
        try {
            return restTemplate.postForObject(url, body, Map.class);
        } catch (Exception e) {
            return Map.of("status", "error", "message", "AI 解析失败：" + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callAiStatus() {
        String url = agentBaseUrl + "/courses/ai-status";
        try {
            return restTemplate.getForObject(url, Map.class);
        } catch (Exception e) {
            return Map.of("processing", false, "done", false, "error", "查询状态失败：" + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callChat(Map<String, Object> body) {
        String url = agentBaseUrl + "/chat";
        try {
            return restTemplate.postForObject(url, body, Map.class);
        } catch (Exception e) {
            return Map.of("reply", "AI 助手暂不可用：" + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callClearCourses() {
        String url = agentBaseUrl + "/courses";
        try {
            restTemplate.delete(url);
            return Map.of("status", "ok", "message", "课表已清空");
        } catch (Exception e) {
            return Map.of("status", "error", "message", "清空失败：" + e.getMessage());
        }
    }
}
