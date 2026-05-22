package com.dayagent.controller;

import com.dayagent.common.Result;
import com.dayagent.context.UserContext;
import com.dayagent.entity.Goal;
import com.dayagent.mapper.GoalMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/goal")
@RequiredArgsConstructor
public class GoalController {

    private final GoalMapper goalMapper;

    @PostMapping
    public Result<?> createGoal(@RequestBody Goal goal) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        goal.setUserId(userId);
        goal.setStatus("active");
        goalMapper.insert(goal);
        return Result.success("目标创建成功");
    }

    @GetMapping
    public Result<List<Goal>> listGoals() {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        List<Goal> list = goalMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<Goal>()
                        .eq(Goal::getUserId, userId)
        );
        return Result.success(list);
    }

    @PutMapping("/{id}")
    public Result<?> updateGoal(@PathVariable Long id, @RequestBody Goal goal) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        Goal existing = goalMapper.selectById(id);
        if (existing == null || !existing.getUserId().equals(userId)) {
            return Result.error(404, "目标不存在");
        }
        if (goal.getContent() != null) existing.setContent(goal.getContent());
        if (goal.getEndDate() != null) existing.setEndDate(goal.getEndDate());
        if (goal.getStatus() != null) existing.setStatus(goal.getStatus());
        if (goal.getType() != null) existing.setType(goal.getType());
        if (goal.getStartDate() != null) existing.setStartDate(goal.getStartDate());
        goalMapper.updateById(existing);
        return Result.success("目标更新成功");
    }

    @DeleteMapping("/{id}")
    public Result<?> deleteGoal(@PathVariable Long id) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        Goal existing = goalMapper.selectById(id);
        if (existing == null || !existing.getUserId().equals(userId)) {
            return Result.error(404, "目标不存在");
        }
        goalMapper.deleteById(id);
        return Result.success("目标删除成功");
    }
}
