package com.dayagent.handler;

import com.dayagent.common.BusinessException;
import com.dayagent.common.Result;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.security.SignatureException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理，返回统一 Result 格式
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BusinessException.class)
    public Result<?> handleBusinessException(BusinessException e) {
        log.warn("业务异常: code={}, message={}", e.getCode(), e.getMessage());
        return Result.error(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(ExpiredJwtException.class)
    public Result<?> handleExpiredJwt(ExpiredJwtException e) {
        return Result.error(401, "Token 已过期，请重新登录");
    }

    @ExceptionHandler({SignatureException.class, MalformedJwtException.class})
    public Result<?> handleInvalidJwt(Exception e) {
        return Result.error(401, "Token 无效");
    }

    @ExceptionHandler(RuntimeException.class)
    public Result<?> handleRuntimeException(RuntimeException e) {
        log.error("未预期的运行时异常", e);
        return Result.error(500, "服务器内部错误: " + e.getMessage());
    }

    @ExceptionHandler(Exception.class)
    public Result<?> handleException(Exception e) {
        log.error("未知异常", e);
        return Result.error(500, "服务器内部错误");
    }
}
