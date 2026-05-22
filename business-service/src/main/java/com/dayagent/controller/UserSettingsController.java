package com.dayagent.controller;

import com.dayagent.common.Result;
import com.dayagent.context.UserContext;
import com.dayagent.entity.UserSettings;
import com.dayagent.service.UserSettingsService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/user/settings")
@RequiredArgsConstructor
public class UserSettingsController {

    private final UserSettingsService settingsService;

    @GetMapping
    public Result<?> getSettings() {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        UserSettings settings = settingsService.getByUserId(userId);
        return Result.success(settingsService.buildSettingsMapMasked(settings));
    }

    @PutMapping
    public Result<?> updateSettings(@RequestBody Map<String, Object> updates) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        settingsService.updateSettings(userId, updates);
        return Result.success("ok");
    }
}
