package com.dayagent.config;

import com.dayagent.mqtt.SensorWebSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

/**
 * WebSocket 配置
 * 注册 /ws/sensor 端点，浏览器连接后就能收到实时传感器数据
 */
@Configuration
@EnableWebSocket   // 开启 WebSocket 功能
public class WebSocketConfig implements WebSocketConfigurer {

    private final SensorWebSocketHandler handler;

    public WebSocketConfig(SensorWebSocketHandler handler) {
        this.handler = handler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(handler, "/ws/sensor")   // 浏览器连接 ws://localhost:8080/ws/sensor
                .setAllowedOriginPatterns("*");        // 允许跨域
    }
}
