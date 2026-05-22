package com.dayagent.controller;

import com.dayagent.common.Result;
import com.dayagent.context.UserContext;
import com.dayagent.service.AgentCallerService;
import com.dayagent.service.PlanResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class PlanController {

    private final AgentCallerService agentCallerService;

    @GetMapping("/plan")
    public Result<PlanResponse> getPlan(
            @RequestParam(defaultValue = "南昌") String location,
            @RequestParam(defaultValue = "false") boolean forceRefresh
    ) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) userId = 1L;

        // 非强制刷新时，优先返回今天已缓存的规划
        if (!forceRefresh) {
            PlanResponse cached = agentCallerService.getCachedPlan(userId);
            if (cached != null) {
                return Result.success(cached);
            }
        }

        PlanResponse plan = agentCallerService.generatePlan(userId, location);
        return Result.success(plan);
    }
}
