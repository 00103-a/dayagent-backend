#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <driver/i2s.h>

#define I2S_BCLK  5
#define I2S_LRC   15
#define I2S_DIN   16
#define I2S_DOUT  8

#define SAMPLE_RATE  16000
#define REC_SEC      3
#define REC_SAMPLES  (SAMPLE_RATE * REC_SEC)
#define VAD_LEVEL    3000000

const char* WIFI_SSID = "菠萝手机";
const char* WIFI_PASS = "12345678";
const char* SERVER_URL = "http://10.130.249.183:8000/voice/chat";

int16_t* recBuf = nullptr;

void setup() {
  Serial.begin(115200);
  delay(1000);

  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_RX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;

  i2s_pin_config_t pin = {};
  pin.bck_io_num = I2S_BCLK;
  pin.ws_io_num = I2S_LRC;
  pin.data_in_num = I2S_DIN;
  pin.data_out_num = I2S_DOUT;

  i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin);
  i2s_zero_dma_buffer(I2S_NUM_0);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int t = 0;
  while (WiFi.status() != WL_CONNECTED && t < 30) { delay(1000); t++; }
  Serial.println(WiFi.status() == WL_CONNECTED ? "WiFi OK" : "WiFi FAIL");

  recBuf = (int16_t*)malloc(REC_SAMPLES * 2);
  Serial.println("Ready - say '樊玉明你好'");
}

void loop() {
  int32_t buf[256];
  static int recIdx = 0;
  static bool recording = false;
  size_t r = 0, w = 0;

  i2s_read(I2S_NUM_0, buf, sizeof(buf), &r, portMAX_DELAY);
  int cnt = r / 4;

  // 算峰值
  int32_t peak = 0;
  for (int i = 0; i < cnt; i++) if (abs(buf[i]) > peak) peak = abs(buf[i]);

  // 触发录音
  if (!recording && peak > VAD_LEVEL) {
    recording = true;
    recIdx = 0;
    Serial.println("REC");
  }

  // 录音中
  if (recording) {
    for (int i = 0; i < cnt && recIdx < REC_SAMPLES; i++)
      recBuf[recIdx++] = buf[i] >> 14;

    // 录满 → 发 HTTP
    if (recIdx >= REC_SAMPLES) {
      recording = false;
      Serial.println("SEND");

      WiFiClient client;
      HTTPClient http;
      http.begin(client, SERVER_URL);
      http.addHeader("Content-Type", "application/octet-stream");
      int code = http.POST((uint8_t*)recBuf, REC_SAMPLES * 2);
      Serial.println(code);

      if (code == 200) {
        int len = http.getSize();
        if (len > 0 && len < REC_SAMPLES * 4) {
          WiFiClient* stream = http.getStreamPtr();
          int16_t* playBuf = (int16_t*)malloc(len);
          stream->readBytes((uint8_t*)playBuf, len);
          Serial.println("PLAY");

          for (int pos = 0; pos < len / 2; pos++) {
            int32_t s = ((int32_t)playBuf[pos]) << 14;
            size_t ww = 0;
            i2s_write(I2S_NUM_0, &s, 4, &ww, portMAX_DELAY);
          }
          free(playBuf);
        }
      }
      http.end();
      Serial.println("OK");
      delay(500);
    }

    // 录音时写静音到 TX
    memset(buf, 0, cnt * 4);
  }

  // 正常环回（录音时为静音）
  i2s_write(I2S_NUM_0, buf, cnt * 4, &w, portMAX_DELAY);
}
