package com.dayagent.config;

import jakarta.annotation.PostConstruct;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

/**
 * JWT 工具 — 静态方法模式，供拦截器和 Controller 直接调用
 */
@Component
public class JwtUtils {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.expiration}")
    private long expirationMs;

    private static SecretKey KEY;
    private static long EXPIRATION_MS;

    @PostConstruct
    public void init() {
        KEY = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        EXPIRATION_MS = expirationMs;
    }

    /** 生成 Access Token，主题存 user_id 字符串 */
    public static String generateAccessToken(Long userId) {
        Date now = new Date();
        return Jwts.builder()
                .subject(String.valueOf(userId))
                .issuedAt(now)
                .expiration(new Date(now.getTime() + EXPIRATION_MS))
                .signWith(KEY)
                .compact();
    }

    /** 从 token 解析 user_id */
    public static Long getUserIdFromToken(String token) {
        Claims claims = Jwts.parser()
                .verifyWith(KEY)
                .build()
                .parseSignedClaims(token)
                .getPayload();
        return Long.valueOf(claims.getSubject());
    }

    /** 验证 token 是否有效 */
    public static boolean validateToken(String token) {
        try {
            getUserIdFromToken(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    /**
     * 验证并解析 Access Token — 供 JwtInterceptor 使用
     * JWT 异常原样上抛，由 GlobalExceptionHandler 返回 401
     */
    public static Long resolveAndValidateAccessToken(String token) {
        // getUserIdFromToken 内部会抛 ExpiredJwtException 等，
        // 让 GlobalExceptionHandler 对应的 401 handler 处理
        return getUserIdFromToken(token);
    }
}
