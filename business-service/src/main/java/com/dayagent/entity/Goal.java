package com.dayagent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;

@Data
@TableName("goal")
public class Goal {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String type;      // "weekly" 或 "monthly"
    private String content;
    private LocalDate startDate;
    private LocalDate endDate;
    private String status;    // "active" 或 "done"
}
