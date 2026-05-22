package com.dayagent.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * RestTemplate Bean 配置
 *
 * 超时设置对应 CLAUDE.md 规范：连 5s，读 10s。
 * 使用 JDK 内置 URLConnection（不引入 httpclient5 额外依赖）。
 */
@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);   // 建立连接超时 5 秒
        factory.setReadTimeout(120_000);   // 等待响应超时 120 秒（LLM + 多源抓取耗时较长，DeepSeek 可能 >60s）

        return new RestTemplate(factory);
    }
}
