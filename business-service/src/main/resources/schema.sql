-- DayAgent 数据库初始化脚本
-- 先创建数据库：CREATE DATABASE dayagent DEFAULT CHARACTER SET utf8mb4;

-- 用户表
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL COMMENT 'BCrypt加密',
    wechat_work_id VARCHAR(100) COMMENT '企业微信推送ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 每日总结
CREATE TABLE daily_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    summary_date DATE NOT NULL,
    content TEXT NOT NULL,
    mood_score TINYINT COMMENT '精力评分 1-5，1=😫 5=🔥',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, summary_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户目标
CREATE TABLE goal (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    type ENUM('weekly', 'monthly') NOT NULL,
    content VARCHAR(500) NOT NULL,
    start_date DATE,
    end_date DATE,
    status ENUM('active', 'done') DEFAULT 'active',
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 快递单号
CREATE TABLE parcel (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    tracking_no VARCHAR(100) NOT NULL,
    carrier VARCHAR(50) COMMENT '快递公司，如顺丰、京东',
    remark VARCHAR(100) COMMENT '备注，如"耳机"',
    status VARCHAR(200) COMMENT '最新物流状态',
    track_details TEXT COMMENT '完整物流轨迹JSON',
    last_checked DATETIME,
    is_delivered BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_delivered (user_id, is_delivered)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 每日规划缓存
CREATE TABLE daily_plan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    plan_date DATE NOT NULL,
    content TEXT NOT NULL,
    raw_data JSON COMMENT '多源数据快照',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_plan_date (user_id, plan_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
