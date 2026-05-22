package com.dayagent.controller;

import com.dayagent.common.Result;
import com.dayagent.context.UserContext;
import com.dayagent.entity.Parcel;
import com.dayagent.mapper.ParcelMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/parcel")
@RequiredArgsConstructor
public class ParcelController {

    private final ParcelMapper parcelMapper;

    @PostMapping
    public Result<?> addParcel(@RequestBody Parcel parcel) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        if (parcel.getTrackingNo() == null || parcel.getTrackingNo().isBlank()) {
            return Result.error(400, "快递单号不能为空");
        }
        if (parcel.getCarrier() == null || parcel.getCarrier().isBlank()) {
            return Result.error(400, "快递公司不能为空");
        }
        parcel.setUserId(userId);
        parcel.setIsDelivered(false);
        parcel.setStatus("待查询");
        parcelMapper.insert(parcel);
        return Result.success("快递单号添加成功");
    }

    @GetMapping
    public Result<List<Parcel>> listParcels() {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        List<Parcel> list = parcelMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<Parcel>()
                        .eq(Parcel::getUserId, userId)
                        .orderByDesc(Parcel::getCreatedAt)
        );
        return Result.success(list);
    }

    @GetMapping("/{id}/refresh")
    public Result<Parcel> refreshParcel(@PathVariable Long id) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        Parcel parcel = parcelMapper.selectById(id);
        if (parcel == null || !parcel.getUserId().equals(userId)) {
            return Result.error(404, "快递单号不存在");
        }
        return Result.success(parcel);
    }

    @DeleteMapping("/{id}")
    public Result<?> deleteParcel(@PathVariable Long id) {
        Long userId = UserContext.getCurrentUser();
        if (userId == null) {
            return Result.error(401, "未登录");
        }
        Parcel parcel = parcelMapper.selectById(id);
        if (parcel == null || !parcel.getUserId().equals(userId)) {
            return Result.error(404, "快递单号不存在");
        }
        parcelMapper.deleteById(id);
        return Result.success("快递单号已删除");
    }
}
