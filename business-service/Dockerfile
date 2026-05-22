# ============ Stage 1: Build ============
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build

# 先复制 pom.xml，利用 Docker 缓存层加速重复构建
COPY pom.xml .
RUN mvn dependency:go-offline -B

# 复制源码并打包
COPY src ./src
RUN mvn package -DskipTests -B

# ============ Stage 2: Run ============
FROM eclipse-temurin:17-jre

WORKDIR /app

# 从构建阶段复制 JAR
COPY --from=builder /build/target/business-service-0.1.0.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
