package com.dayagent.controller;

import com.dayagent.common.Result;
import com.dayagent.entity.DailySummary;
import com.dayagent.mapper.DailySummaryMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/summary")
@RequiredArgsConstructor
public class SummaryController {

    private static final Long DEFAULT_USER_ID = 1L;
    private final DailySummaryMapper dailySummaryMapper;

    @PostMapping
    public Result<?> createSummary(@RequestBody DailySummary summary) {
        summary.setUserId(DEFAULT_USER_ID);
        summary.setSummaryDate(LocalDate.now());
        dailySummaryMapper.insert(summary);
        return Result.success("总结保存成功");
    }

    @GetMapping
    public Result<List<DailySummary>> listSummaries() {
        List<DailySummary> list = dailySummaryMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<DailySummary>()
                        .eq(DailySummary::getUserId, DEFAULT_USER_ID)
                        .orderByDesc(DailySummary::getSummaryDate)
        );
        return Result.success(list);
    }

    @PutMapping("/{id}")
    public Result<?> updateSummary(@PathVariable Long id, @RequestBody DailySummary summary) {
        DailySummary existing = dailySummaryMapper.selectById(id);
        if (existing == null || !existing.getUserId().equals(DEFAULT_USER_ID)) {
            return Result.error(404, "总结不存在");
        }
        existing.setContent(summary.getContent());
        if (summary.getMoodScore() != null) {
            existing.setMoodScore(summary.getMoodScore());
        }
        dailySummaryMapper.updateById(existing);
        return Result.success("总结更新成功");
    }

    @DeleteMapping("/{id}")
    public Result<?> deleteSummary(@PathVariable Long id) {
        DailySummary existing = dailySummaryMapper.selectById(id);
        if (existing == null || !existing.getUserId().equals(DEFAULT_USER_ID)) {
            return Result.error(404, "总结不存在");
        }
        dailySummaryMapper.deleteById(id);
        return Result.success("总结删除成功");
    }
}
