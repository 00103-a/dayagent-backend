package com.dayagent.controller;

import com.dayagent.common.Result;
import com.dayagent.config.JwtUtils;
import com.dayagent.entity.User;
import com.dayagent.mapper.UserMapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {

    private final UserMapper userMapper;
    private final BCryptPasswordEncoder passwordEncoder;

    @PostMapping("/register")
    public Result<?> register(@RequestBody User user) {
        if (user.getUsername() == null || user.getUsername().isBlank()) {
            return Result.error(400, "用户名不能为空");
        }
        if (user.getPassword() == null || user.getPassword().isBlank()) {
            return Result.error(400, "密码不能为空");
        }
        if (user.getPassword().length() < 6) {
            return Result.error(400, "密码长度至少 6 位");
        }
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        try {
            userMapper.insert(user);
        } catch (DuplicateKeyException e) {
            return Result.error(400, "用户名已存在");
        }
        return Result.success("注册成功");
    }

    @PostMapping("/login")
    public Result<?> login(@RequestBody User loginReq) {
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getUsername, loginReq.getUsername())
        );
        if (user == null) {
            return Result.error(401, "用户名或密码错误");
        }
        if (!passwordEncoder.matches(loginReq.getPassword(), user.getPassword())) {
            return Result.error(401, "用户名或密码错误");
        }
        String token = JwtUtils.generateAccessToken(user.getId());
        return Result.success(Map.of(
                "token", token,
                "userId", user.getId(),
                "username", user.getUsername()
        ));
    }
}
