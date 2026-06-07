package com.dayagent.mqtt;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;

/**
 * WebSocket 消息处理器
 * 管理所有连上来的浏览器，负责广播传感器数据
 */
@Component
public class SensorWebSocketHandler extends TextWebSocketHandler {  // ← 必须继承 TextWebSocketHandler

    private static final Logger log = LoggerFactory.getLogger(SensorWebSocketHandler.class);

    // 存所有"正在连接"的浏览器，相当于微信群成员列表
    private static final Set<WebSocketSession> sessions = new CopyOnWriteArraySet<>();

    /**
     * 浏览器连上以后
     * session = 这个浏览器的连接，可以靠它给这个浏览器发消息
     */
    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);
        log.info("[WebSocket] 浏览器连入，当前连接数: {}", sessions.size());
    }

    /**
     * 浏览器断开以后
     * status = 断开原因（正常关闭？网络断了？超时？）
     */
    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);
        log.info("[WebSocket] 浏览器断开，当前连接数: {}", sessions.size());
    }

    /**
     * 广播消息给所有在线的浏览器
     * MqttSubscriber 收到传感器数据后会调这个方法
     */
    public void broadcast(String message) {
        TextMessage textMessage = new TextMessage(message);
        for (WebSocketSession session : sessions) {
            try {
                if (session.isOpen()) {
                    session.sendMessage(textMessage);  // 给这个浏览器发消息
                }
            } catch (IOException e) {
                log.warn("[WebSocket] 推送失败: {}", e.getMessage());
            }
        }
    }

    public int getConnectionCount() {
        return sessions.size();
    }
}
