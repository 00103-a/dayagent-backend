package com.dayagent.context;

/**
 * 基于 ThreadLocal 的当前用户持有者
 * 请求进入时由 JwtInterceptor 设置，请求结束时清理
 */
public class UserContext {

    private static final ThreadLocal<Long> USER_HOLDER = new ThreadLocal<>();

    public static void setCurrentUser(Long userId) {
        USER_HOLDER.set(userId);
    }

    public static Long getCurrentUser() {
        return USER_HOLDER.get();
    }

    public static void clear() {
        USER_HOLDER.remove();
    }
}
