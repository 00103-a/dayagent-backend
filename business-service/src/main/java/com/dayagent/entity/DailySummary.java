package com.dayagent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("daily_summary")
public class DailySummary {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private LocalDate summaryDate;
    private String content;
    private Integer moodScore;
    private LocalDateTime createdAt;
}
