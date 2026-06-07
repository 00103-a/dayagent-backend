package com.dayagent.config;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
public class MqttConfig {
    /**
   * MQTT 客户端配置
   * 使用 Eclipse Paho 原生 API 连接 Mosquitto Broker
   */
   @Value("${mqtt.broker-url}")
   private String brokerUrl;

   @Value("${mqtt.client-id}")
   private String clientId;

   @Bean
   public MqttConnectOptions mqttConnectOptions(){
    MqttConnectOptions options = new MqttConnectOptions();
    options.setAutomaticReconnect(true);
    options.setCleanSession(true);
    options.setConnectionTimeout(10);
    options.setKeepAliveInterval(60);
    return options;
   }

   @Bean
   public MqttClient mqttClient(MqttConnectOptions options) throws MqttException{
    MqttClient client = new MqttClient(brokerUrl, clientId);
    client.connect(options);
    return client;
   }
    

  
}
