package com.dayagent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("daily_plan")
public class DailyPlan {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private LocalDate planDate;
    private String content;       // 规划文本
    private String rawData;       // JSON，存储多源数据快照
    private LocalDateTime createdAt;
}
