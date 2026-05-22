package com.dayagent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("user_settings")
public class UserSettings {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String llmApiKey;
    private String llmBaseUrl;
    private String llmModel;
    private String weatherApiKey;
    private String newsApiKey;
    private String kuaidi100Customer;
    private String kuaidi100Key;
    private String chaoxingUsername;
    private String chaoxingPassword;
    private String defaultLocation;
    private String semesterStart;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
