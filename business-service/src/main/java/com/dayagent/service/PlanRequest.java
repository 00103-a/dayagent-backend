package com.dayagent.service;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 发给 Python /generate-plan 的请求体
 *
 * Java 用驼峰命名, Python 用下划线命名.
 * @JsonProperty 让 Jackson 序列化时转为 Python 期望的字段名.
 */
@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)  // 不序列化 null 字段，让 Python 用默认值
public class PlanRequest {
    @JsonProperty("user_id")
    private String userId;

    @JsonProperty("yesterday_summary")
    private String yesterdaySummary;

    private List<String> goals;       // 刚好同名, 不用转
    private String location;          // 刚好同名, 不用转

    @JsonProperty("force_refresh")
    private Boolean forceRefresh;     // 跳过缓存，强制重新抓取

    private List<ParcelInfo> parcels; // 用户未签收的快递列表

    @JsonProperty("user_settings")
    private Map<String, Object> userSettings;

    @Data
    @Builder
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class ParcelInfo {
        @JsonProperty("tracking_no")
        private String trackingNo;

        private String carrier;       // 快递公司
        private String remark;        // 备注
    }
}
