package com.dayagent.controller;

import com.dayagent.context.UserContext;
import com.dayagent.service.ChatService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    @PostMapping
    public ResponseEntity<Map<String, Object>> chat(@RequestBody Map<String, Object> body) {
        // Chat 必须绑定当前登录用户。这样后续 ChatService 查询目标/总结/规划时，
        // 使用的是后端鉴权后的 userId，而不是前端传来的不可信 userId。
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of("error", "未登录"));
        }
        // Controller 不拼上下文、不调用 Python；这些业务编排交给 ChatService。
        return ResponseEntity.ok(chatService.chat(userId, body));
    }
}
