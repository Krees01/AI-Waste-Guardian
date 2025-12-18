#include <WiFi.h>
#include "esp_http_server.h"


const char* ssid = "test";      
const char* password = "jak221106";

#define FLASH_LAMP 4    
#define INTERNAL_LED 33 

httpd_handle_t server = NULL;

static esp_err_t cmd_handler(httpd_req_t *req) {
  char* buf; size_t buf_len; char variable[32] = {0,};
  buf_len = httpd_req_get_url_query_len(req) + 1;
  
  if (buf_len > 1) {
    buf = (char*)malloc(buf_len);
    if (httpd_req_get_url_query_str(req, buf, buf_len) == ESP_OK) {
      if (httpd_query_key_value(buf, "action", variable, sizeof(variable)) == ESP_OK) {
        int val = atoi(variable);
        

        if(val == 1) { 

            digitalWrite(FLASH_LAMP, HIGH);     
            digitalWrite(INTERNAL_LED, LOW);   
            Serial.println(">>> PERINTAH: NYALA (ON)");
        } 
        else { 
            // ACTION 0: MATI (OFF)
            digitalWrite(FLASH_LAMP, LOW);       
            digitalWrite(INTERNAL_LED, HIGH);   
            Serial.println(">>> PERINTAH: MATI (OFF)");
        }
      }
    }
    free(buf);
  }
  httpd_resp_send(req, "OK", 2);
  return ESP_OK;
}

void startServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  httpd_uri_t cmd_uri = { .uri = "/control", .method = HTTP_GET, .handler = cmd_handler, .user_ctx = NULL };
  if (httpd_start(&server, &config) == ESP_OK) {
      httpd_register_uri_handler(server, &cmd_uri);
  }
}

void setup() {
  Serial.begin(115200);
  

  pinMode(FLASH_LAMP, OUTPUT);
  pinMode(INTERNAL_LED, OUTPUT);
  

  digitalWrite(FLASH_LAMP, LOW);
  digitalWrite(INTERNAL_LED, HIGH); 

  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print("."); 
  }
  
  Serial.println("");
  Serial.println("Wi-Fi connected!");
  Serial.print("IP address: "); 
  Serial.println(WiFi.localIP()); 
  
  startServer();
}

void loop() { delay(1000); }
