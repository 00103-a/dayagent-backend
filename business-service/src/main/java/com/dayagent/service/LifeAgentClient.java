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
        return callWeather(location, lat, lng, "");
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callWeather(String location, Double lat, Double lng, String apiKey) {
        StringBuilder url = new StringBuilder(agentBaseUrl + "/weather?location=" + location);
        if (lat != null && lng != null) {
            url.append("&lat=").append(lat).append("&lng=").append(lng);
        }
        if (apiKey != null && !apiKey.isEmpty()) {
            url.append("&api_key=").append(apiKey);
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
        return callNews(goals, yesterdaySummary, "", "", "", "");
    }

    public String callNews(String goals, String yesterdaySummary,
                           String llmKey, String llmBaseUrl, String llmModel, String newsApiKey) {
        StringBuilder url = new StringBuilder(
            agentBaseUrl + "/news?goals=" + goals + "&yesterday_summary=" + yesterdaySummary);
        if (llmKey != null && !llmKey.isEmpty()) url.append("&llm_key=").append(llmKey);
        if (llmBaseUrl != null && !llmBaseUrl.isEmpty()) url.append("&llm_base_url=").append(llmBaseUrl);
        if (llmModel != null && !llmModel.isEmpty()) url.append("&llm_model=").append(llmModel);
        if (newsApiKey != null && !newsApiKey.isEmpty()) url.append("&news_api_key=").append(newsApiKey);
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restTemplate.getForObject(url.toString(), Map.class);
            return resp != null ? (String) resp.getOrDefault("news_text", "新闻数据获取失败") : "新闻数据获取失败";
        } catch (Exception e) {
            return "新闻服务暂不可用：" + e.getMessage();
        }
    }

    public String callChaoxingTasks() {
        return callChaoxingTasks("", "");
    }

    public String callChaoxingTasks(String username, String password) {
        StringBuilder url = new StringBuilder(agentBaseUrl + "/chaoxing/tasks");
        if (username != null && !username.isEmpty()) url.append("?username=").append(username);
        if (password != null && !password.isEmpty()) {
            url.append(username != null && !username.isEmpty() ? "&" : "?").append("password=").append(password);
        }
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restTemplate.getForObject(url.toString(), Map.class);
            return resp != null ? (String) resp.getOrDefault("tasks_text", "学习通数据获取失败") : "学习通数据获取失败";
        } catch (Exception e) {
            return "学习通服务暂不可用：" + e.getMessage();
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callListCourses(String week) {
        return callListCourses(week, "", "");
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callListCourses(String week, String semesterStart, String userId) {
        StringBuilder url = new StringBuilder(agentBaseUrl + "/courses");
        boolean hasParam = false;
        if (week != null && !week.isBlank()) {
            url.append("?week=").append(week);
            hasParam = true;
        }
        if (semesterStart != null && !semesterStart.isEmpty()) {
            url.append(hasParam ? "&" : "?").append("semester_start=").append(semesterStart);
            hasParam = true;
        }
        if (userId != null && !userId.isEmpty()) {
            url.append(hasParam ? "&" : "?").append("user_id=").append(userId);
        }
        try {
            return restTemplate.getForObject(url.toString(), Map.class);
        } catch (Exception e) {
            return Map.of("count", 0, "courses", java.util.List.of(), "text", "课表服务暂不可用");
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callImportCourses(String userId, Map<String, Object> body) {
        StringBuilder url = new StringBuilder(agentBaseUrl + "/courses/browser-import");
        if (userId != null && !userId.isEmpty()) {
            url.append("?user_id=").append(userId);
        }
        try {
            Map<String, Object> requestBody = body != null ? body : Map.of();
            return restTemplate.postForObject(url.toString(), requestBody, Map.class);
        } catch (Exception e) {
            return Map.of("status", "error", "message", "Import failed: " + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callAiImportCourses(Map<String, Object> body, String userId) {
        if (userId != null && !userId.isEmpty()) {
            body.put("user_id", userId);
        }
        String url = agentBaseUrl + "/courses/ai-import";
        try {
            return restTemplate.postForObject(url, body, Map.class);
        } catch (Exception e) {
            return Map.of("status", "error", "message", "AI 解析失败：" + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> callAiStatus(String userId) {
        String url = agentBaseUrl + "/courses/ai-status";
        if (userId != null && !userId.isEmpty()) {
            url += "?user_id=" + userId;
        }
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
    public Map<String, Object> callClearCourses(String userId) {
        String url = agentBaseUrl + "/courses";
        if (userId != null && !userId.isEmpty()) {
            url += "?user_id=" + userId;
        }
        try {
            restTemplate.delete(url);
            return Map.of("status", "ok", "message", "课表已清空");
        } catch (Exception e) {
            return Map.of("status", "error", "message", "清空失败：" + e.getMessage());
        }
    }
    
    @SuppressWarnings("unchecked")
    public Map<String, Object> callEnvironmentInsights(String userId){
        StringBuilder url = new StringBuilder(agentBaseUrl + "/environment/insights");
        if(userId != null && !userId.isEmpty()){
            url.append("?user_id=").append(userId);
        }
        try {
            return restTemplate.getForObject(url.toString(),Map.class);
        }catch(Exception e){
            return Map.of("current_readings",null,"alerts",java.util.List.of(),
            "ai_insights","环境服务暂不可用" + e.getMessage());
        }
    }
}
