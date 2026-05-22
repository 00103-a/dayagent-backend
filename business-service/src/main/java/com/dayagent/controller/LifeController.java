package com.dayagent.controller;

import com.dayagent.service.LifeAgentClient;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 生活模块聚合接口：天气、新闻、课表、学习通
 * 所有接口走 Java 代理到 Python，统一 /api/ 前缀 + JWT 鉴权
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class LifeController {

    private final LifeAgentClient lifeAgentClient;

    @GetMapping("/weather")
    public ResponseEntity<Map<String, Object>> getWeather(
            @RequestParam(defaultValue = "北京") String location,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng) {
        Map<String, Object> result = lifeAgentClient.callWeather(location, lat, lng);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/news")
    public ResponseEntity<Map<String, Object>> getNews(
            @RequestParam(defaultValue = "") String goals,
            @RequestParam(defaultValue = "") String summary) {
        String newsText = lifeAgentClient.callNews(goals, summary);
        return ResponseEntity.ok(Map.of("news_text", newsText));
    }

    @GetMapping("/chaoxing/tasks")
    public ResponseEntity<Map<String, Object>> getChaoxingTasks() {
        String tasksText = lifeAgentClient.callChaoxingTasks();
        return ResponseEntity.ok(Map.of("tasks_text", tasksText));
    }

    @GetMapping("/courses")
    public ResponseEntity<Map<String, Object>> listCourses(
            @RequestParam(required = false) String week) {
        Map<String, Object> result = lifeAgentClient.callListCourses(week);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/courses/browser-import")
    public ResponseEntity<Map<String, Object>> importCourses() {
        Map<String, Object> result = lifeAgentClient.callImportCourses();
        return ResponseEntity.ok(result);
    }

    @PostMapping("/courses/import")
    public ResponseEntity<Map<String, Object>> jsonImportCourses(@RequestBody Map<String, Object> body) {
        Map<String, Object> result = lifeAgentClient.callJsonImportCourses(body);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/courses/ai-import")
    public ResponseEntity<Map<String, Object>> aiImportCourses(@RequestBody Map<String, Object> body) {
        Map<String, Object> result = lifeAgentClient.callAiImportCourses(body);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/courses/ai-status")
    public ResponseEntity<Map<String, Object>> aiStatus() {
        Map<String, Object> result = lifeAgentClient.callAiStatus();
        return ResponseEntity.ok(result);
    }

    @PostMapping("/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody Map<String, Object> body) {
        Map<String, Object> result = lifeAgentClient.callChat(body);
        return ResponseEntity.ok(result);
    }

    @DeleteMapping("/courses")
    public ResponseEntity<Map<String, Object>> clearCourses() {
        Map<String, Object> result = lifeAgentClient.callClearCourses();
        return ResponseEntity.ok(result);
    }
}
