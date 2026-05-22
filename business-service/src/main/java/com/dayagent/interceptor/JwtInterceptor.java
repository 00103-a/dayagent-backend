package com.dayagent.interceptor;

import com.dayagent.common.BusinessException;
import com.dayagent.config.JwtUtils;
import com.dayagent.context.UserContext;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.security.SignatureException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * JWT 拦截器 — 在请求进入 Controller 之前校验 Token
 * 不依赖 Spring Security，由 WebConfig 注册到拦截器链
 */
@Component
public class JwtInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        String auth = request.getHeader("Authorization");

        if (auth == null || auth.isBlank()) {
            throw new BusinessException(401, "缺少 Authorization 头");
        }
        if (!auth.startsWith("Bearer ")) {
            throw new BusinessException(401, "Authorization 格式错误，需要 Bearer <token>");
        }

        String token = auth.substring(7);
        try {
            Long userId = JwtUtils.resolveAndValidateAccessToken(token);
            UserContext.setCurrentUser(userId);
            return true;
        } catch (BusinessException e) {
            throw e;
        } catch (ExpiredJwtException e) {
            throw e;
        } catch (SignatureException | MalformedJwtException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException(401, "Token 无效");
        }
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        UserContext.clear();
    }
}
