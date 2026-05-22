package com.dayagent.common;

import lombok.Getter;

/**
 * 业务异常，由 GlobalExceptionHandler 统一处理
 */
@Getter
public class BusinessException extends RuntimeException {

    private final Integer code;

    public BusinessException(Integer code, String message) {
        super(message);
        this.code = code;
    }
}
