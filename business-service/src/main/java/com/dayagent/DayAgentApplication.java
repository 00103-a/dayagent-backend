package com.dayagent;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication

@MapperScan("com.dayagent.mapper")
@EnableScheduling  // 开启定时任务
public class DayAgentApplication {

    public static void main(String[] args){
        SpringApplication.run(DayAgentApplication.class, args);
    }
}
