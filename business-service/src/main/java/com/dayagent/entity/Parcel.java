package com.dayagent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("parcel")
public class Parcel {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String trackingNo;
    private String carrier;       // 快递公司，如"顺丰"、"京东"
    private String remark;        // 备注，如"耳机"
    private String status;        // 最新物流状态文本
    private String trackDetails;  // 完整物流轨迹 JSON
    private LocalDateTime lastChecked;
    private Boolean isDelivered;  // 是否已签收
    private LocalDateTime createdAt;
}
