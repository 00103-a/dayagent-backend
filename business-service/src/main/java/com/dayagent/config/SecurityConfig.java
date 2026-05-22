package com.dayagent.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

/**
 * 仅提供 BCrypt 加密 Bean，不再使用 Spring Security 过滤器链
 * JWT 鉴权由 JwtInterceptor + WebConfig 接管
 */
@Configuration
public class SecurityConfig {

    @Bean
    public BCryptPasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
