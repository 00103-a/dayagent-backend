package com.dayagent.service;

import org.springframework.stereotype.Service;

/**
 * 企业微信机器人推送（第二阶段实现）
 */
@Service
public class PushService {

    /**
     * 推送文本消息到企业微信
     */
    public void pushMessage(Long userId, String content) {
        // TODO: 第二阶段实现
        // 1. 查用户的 wechatWorkId
        // 2. 调 webhook 发送
        System.out.println("推送消息给用户 " + userId + "：" + content);
    }
}
