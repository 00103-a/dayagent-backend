package com.dayagent.controller;

import com.dayagent.context.UserContext;
import com.dayagent.entity.UserSettings;
import com.dayagent.service.LifeAgentClient;
import com.dayagent.service.UserSettingsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class LifeController {

    private final LifeAgentClient lifeAgentClient;
    private final UserSettingsService userSettingsService;

    @GetMapping("/weather")
    public ResponseEntity<Map<String, Object>> getWeather(
            @RequestParam(defaultValue = "北京") String location,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of("error", "未登录"));
        }
        UserSettings settings = userSettingsService.getByUserId(userId);
        String weatherKey = settings.getWeatherApiKey() != null ? settings.getWeatherApiKey() : "";
        System.out.println("[LifeController] weather: userId=" + userId + ", weatherKey=" + (weatherKey.isEmpty() ? "EMPTY" : "SET(len=" + weatherKey.length() + ")"));
        Map<String, Object> result = lifeAgentClient.callWeather(location, lat, lng, weatherKey);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/news")
    public ResponseEntity<Map<String, Object>> getNews(
            @RequestParam(defaultValue = "") String goals,
            @RequestParam(defaultValue = "") String summary) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of("error", "未登录"));
        }
        UserSettings settings = userSettingsService.getByUserId(userId);
        String llmKey = nullToEmpty(settings.getLlmApiKey());
        String llmBase = nullToEmpty(settings.getLlmBaseUrl());
        String llmModel = nullToEmpty(settings.getLlmModel());
        String newsKey = nullToEmpty(settings.getNewsApiKey());
        System.out.println("[LifeController] news: userId=" + userId + ", llmKey=" + (llmKey.isEmpty() ? "EMPTY" : "SET") + ", newsKey=" + (newsKey.isEmpty() ? "EMPTY" : "SET"));
        String newsText = lifeAgentClient.callNews(goals, summary, llmKey, llmBase, llmModel, newsKey);
        return ResponseEntity.ok(Map.of("news_text", newsText));
        
    }

    @GetMapping("/chaoxing/tasks")
    public ResponseEntity<Map<String, Object>> getChaoxingTasks() {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of("error", "未登录"));
        }
        UserSettings settings = userSettingsService.getByUserId(userId);
        String username = nullToEmpty(settings.getChaoxingUsername());
        String password = nullToEmpty(settings.getChaoxingPassword());
        String tasksText = lifeAgentClient.callChaoxingTasks(username, password);
        return ResponseEntity.ok(Map.of("tasks_text", tasksText));
    }

    @GetMapping("/courses")
    public ResponseEntity<Map<String, Object>> listCourses(
            @RequestParam(required = false) String week) {
        Long userId = UserContext.getCurrentUser();
        String semesterStart = "";
        String userIdStr = "";
        if (userId != null) {
            UserSettings settings = userSettingsService.getByUserId(userId);
            semesterStart = nullToEmpty(settings.getSemesterStart());
            userIdStr = String.valueOf(userId);
        }
        Map<String, Object> result = lifeAgentClient.callListCourses(week, semesterStart, userIdStr);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/courses/browser-import")
    public ResponseEntity<Map<String, Object>> importCourses() {
        Long userId = UserContext.getCurrentUser();
        String userIdStr = userId != null ? String.valueOf(userId) : "";
        Map<String, Object> result = lifeAgentClient.callImportCourses(userIdStr);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/courses/ai-import")
    public ResponseEntity<Map<String, Object>> aiImportCourses(@RequestBody Map<String, Object> body) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of("error", "未登录"));
        }
        UserSettings settings = userSettingsService.getByUserId(userId);
        body.put("llm_api_key", nullToEmpty(settings.getLlmApiKey()));
        body.put("llm_base_url", nullToEmpty(settings.getLlmBaseUrl()));
        body.put("llm_model", nullToEmpty(settings.getLlmModel()));
        body.put("user_id", String.valueOf(userId));
        Map<String, Object> result = lifeAgentClient.callAiImportCourses(body, String.valueOf(userId));
        return ResponseEntity.ok(result);
    }

    @GetMapping("/courses/ai-status")
    public ResponseEntity<Map<String, Object>> aiStatus() {
        Long userId = UserContext.getCurrentUser();
        String userIdStr = userId != null ? String.valueOf(userId) : "";
        Map<String, Object> result = lifeAgentClient.callAiStatus(userIdStr);
        return ResponseEntity.ok(result);
    }

    @DeleteMapping("/courses")
    public ResponseEntity<Map<String, Object>> clearCourses() {
        Long userId = UserContext.getCurrentUser();
        String userIdStr = userId != null ? String.valueOf(userId) : "";
        Map<String, Object> result = lifeAgentClient.callClearCourses(userIdStr);
        return ResponseEntity.ok(result);
    }
    
    @GetMapping("/environment/insights")
    public ResponseEntity<Map<String, Object>> getEnvironmentInsights() {
        Long userId = UserContext.getCurrentUser();
        String userIdStr = userId != null ? String.valueOf(userId) : "";
        Map<String,Object> result = lifeAgentClient.callEnvironmentInsights(userIdStr);
        return ResponseEntity.ok(result);
    }

    private static String nullToEmpty(String s) {
        return s != null ? s : "";
    }
}

