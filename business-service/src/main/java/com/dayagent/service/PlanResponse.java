package com.dayagent.service;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * Python 端 /generate-plan 返回的响应体
 */
@Data
public class PlanResponse {
    private String plan;
    private List<String> priorities;
    private List<String> warnings;
    private List<ParcelStatus> parcels;  // 最新的快递状态

    @Data
    public static class ParcelStatus {
        @JsonProperty("tracking_no")
        private String trackingNo;

        private String carrier;
        private String remark;
        private String state;

        @JsonProperty("is_delivered")
        private Boolean isDelivered;

        @JsonProperty("pickup_code")
        private String pickupCode;

        @JsonProperty("is_waiting_pickup")
        private Boolean isWaitingPickup;

        @JsonProperty("latest_context")
        private String latestContext;

        @JsonProperty("latest_time")
        private String latestTime;

        @JsonProperty("details")
        private List<Map<String, String>> details;
    }
}
