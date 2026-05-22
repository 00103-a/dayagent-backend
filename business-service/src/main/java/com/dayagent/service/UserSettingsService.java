package com.dayagent.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.dayagent.entity.UserSettings;
import com.dayagent.mapper.UserSettingsMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class UserSettingsService {

    private final UserSettingsMapper mapper;

    public UserSettings getByUserId(Long userId) {
        UserSettings settings = mapper.selectOne(
                new LambdaQueryWrapper<UserSettings>()
                        .eq(UserSettings::getUserId, userId)
        );
        if (settings == null) {
            settings = new UserSettings();
            settings.setUserId(userId);
            settings.setLlmBaseUrl("https://api.deepseek.com");
            settings.setLlmModel("deepseek-v4-pro");
            settings.setDefaultLocation("南昌");
        }
        return settings;
    }

    public void updateSettings(Long userId, Map<String, Object> updates) {
        UserSettings current = getByUserId(userId);
        boolean isNew = current.getId() == null;

        if (updates.containsKey("llm_api_key")) {
            current.setLlmApiKey((String) updates.get("llm_api_key"));
        }
        if (updates.containsKey("llm_base_url")) {
            current.setLlmBaseUrl((String) updates.get("llm_base_url"));
        }
        if (updates.containsKey("llm_model")) {
            current.setLlmModel((String) updates.get("llm_model"));
        }
        if (updates.containsKey("weather_api_key")) {
            current.setWeatherApiKey((String) updates.get("weather_api_key"));
        }
        if (updates.containsKey("news_api_key")) {
            current.setNewsApiKey((String) updates.get("news_api_key"));
        }
        if (updates.containsKey("kuaidi100_customer")) {
            current.setKuaidi100Customer((String) updates.get("kuaidi100_customer"));
        }
        if (updates.containsKey("kuaidi100_key")) {
            current.setKuaidi100Key((String) updates.get("kuaidi100_key"));
        }
        if (updates.containsKey("chaoxing_username")) {
            current.setChaoxingUsername((String) updates.get("chaoxing_username"));
        }
        if (updates.containsKey("chaoxing_password")) {
            current.setChaoxingPassword((String) updates.get("chaoxing_password"));
        }
        if (updates.containsKey("default_location")) {
            current.setDefaultLocation((String) updates.get("default_location"));
        }
        if (updates.containsKey("semester_start")) {
            current.setSemesterStart((String) updates.get("semester_start"));
        }

        current.setUpdatedAt(LocalDateTime.now());
        if (isNew) {
            current.setCreatedAt(LocalDateTime.now());
            mapper.insert(current);
        } else {
            mapper.updateById(current);
        }
    }

    public Map<String, Object> buildSettingsMap(UserSettings s) {
        Map<String, Object> map = new HashMap<>();
        map.put("llm_api_key", mask(s.getLlmApiKey()));
        map.put("llm_base_url", s.getLlmBaseUrl());
        map.put("llm_model", s.getLlmModel());
        map.put("weather_api_key", mask(s.getWeatherApiKey()));
        map.put("news_api_key", mask(s.getNewsApiKey()));
        map.put("kuaidi100_customer", mask(s.getKuaidi100Customer()));
        map.put("kuaidi100_key", mask(s.getKuaidi100Key()));
        map.put("chaoxing_username", s.getChaoxingUsername());
        map.put("chaoxing_password", mask(s.getChaoxingPassword()));
        map.put("default_location", s.getDefaultLocation());
        map.put("semester_start", s.getSemesterStart());
        return map;
    }

    private String mask(String value) {
        if (value == null || value.isEmpty()) return "";
        if (value.length() <= 4) return "****";
        return "***" + value.substring(value.length() - 4);
    }
}
