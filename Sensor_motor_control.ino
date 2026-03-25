#include <WiFi.h>
#include <WebServer.h>
#include <DHT.h>

const char* ssid = "Tushar's Galaxy F41";
const char* password = "tushar6574";

WebServer server(80);

// Motor pins
#define IN1 26
#define IN2 27
#define IN3 14
#define IN4 12

// Sensors
#define TRIG 5
#define ECHO 18
#define GAS 34
#define DHTPIN 4
#define BUZZER 2

DHT dht(DHTPIN, DHT11);

// States
bool autoMode = false;
bool humanDetectedFlag = false;

unsigned long lastActionTime = 0;
unsigned long lastBuzzerTime = 0;

// ---------- Motor functions ----------
void forward() { digitalWrite(IN1,HIGH); digitalWrite(IN2,LOW); digitalWrite(IN3,HIGH); digitalWrite(IN4,LOW); }
void backward(){ digitalWrite(IN1,LOW); digitalWrite(IN2,HIGH); digitalWrite(IN3,LOW); digitalWrite(IN4,HIGH); }
void left()    { digitalWrite(IN1,LOW); digitalWrite(IN2,HIGH); digitalWrite(IN3,HIGH); digitalWrite(IN4,LOW); }
void right()   { digitalWrite(IN1,HIGH); digitalWrite(IN2,LOW); digitalWrite(IN3,LOW); digitalWrite(IN4,HIGH); }
void stopRobot(){ digitalWrite(IN1,LOW); digitalWrite(IN2,LOW); digitalWrite(IN3,LOW); digitalWrite(IN4,LOW); }

// ---------- Distance ----------
float getDistance(){
  digitalWrite(TRIG, LOW); delayMicroseconds(2);
  digitalWrite(TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duration = pulseIn(ECHO, HIGH, 30000);
  return duration * 0.034 / 2;
}

// ---------- Web UI ----------
void handleRoot(){
  String page = "<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  page += "<script>function send(c){fetch('/'+c);}</script></head><body>";
  page += "<h1>UGV Disaster Rover</h1>";

  page += "<h3>Status: " + String(autoMode ? "AUTONOMOUS" : "MANUAL") + "</h3>";
  if(humanDetectedFlag) page += "<h2 style='color:red;'>VICTIM SPOTTED!</h2>";

  page += "<button onmousedown=\"send('forward')\" onmouseup=\"send('stop')\">Forward</button><br>";
  page += "<button onclick=\"send('left')\">Left</button>";
  page += "<button onclick=\"send('stop')\">STOP</button>";
  page += "<button onclick=\"send('right')\">Right</button><br>";
  page += "<button onclick=\"send('back')\">Backward</button><hr>";

  page += "<button onclick=\"send('auto')\">Enable Auto</button>";
  page += "<button onclick=\"send('manual')\">Enable Manual</button>";

  page += "</body></html>";
  server.send(200, "text/html", page);
}

// ---------- Setup ----------
void setup(){
  Serial.begin(115200);

  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(GAS, INPUT);
  pinMode(BUZZER, OUTPUT);

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected: " + WiFi.localIP().toString());

  dht.begin();

  // Routes
  server.on("/", handleRoot);

  server.on("/forward", [](){ forward(); server.send(200); });
  server.on("/back",    [](){ backward(); server.send(200); });
  server.on("/left",    [](){ left(); server.send(200); });
  server.on("/right",   [](){ right(); server.send(200); });
  server.on("/stop",    [](){ stopRobot(); server.send(200); });

  // AI Trigger
  server.on("/victim", [](){
    humanDetectedFlag = true;
    autoMode = false;
    stopRobot();
    server.send(200, "text/plain", "Alert Received");
  });

  server.on("/auto", [](){ autoMode = true; server.send(200); });

  server.on("/manual", [](){
    autoMode = false;
    humanDetectedFlag = false;
    digitalWrite(BUZZER, LOW);
    stopRobot();
    server.send(200);
  });

  // Sensor API
  server.on("/data", [](){
    float dist = getDistance();
    int gas = analogRead(GAS);
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();

    String json = "{";
    json += "\"distance\":" + String(dist) + ",";
    json += "\"gas\":" + String(gas) + ",";
    json += "\"temp\":" + String(temp) + ",";
    json += "\"humidity\":" + String(hum);
    json += "}";

    server.send(200, "application/json", json);
  });

  server.begin();
}

// ---------- Loop ----------
void loop(){
  server.handleClient();

  //1. AI OVERRIDE (HIGHEST PRIORITY)
  if(humanDetectedFlag){
    stopRobot();

    // Blinking buzzer
    if(millis() % 500 < 250){
      digitalWrite(BUZZER, HIGH);
    } else {
      digitalWrite(BUZZER, LOW);
    }
    return;
  }

  //2. GAS SAFETY
  int gasValue = analogRead(GAS);
  if(gasValue > 3000){
    stopRobot();
    digitalWrite(BUZZER, HIGH);
    return;
  }

  //3. NON-BLOCKING AUTO MODE
  if(autoMode){
    float dist = getDistance();
    unsigned long currentTime = millis();

    if(dist > 0 && dist < 25){
      if(currentTime - lastActionTime < 300){
        stopRobot();
      }
      else if(currentTime - lastActionTime < 800){
        backward();
      }
      else if(currentTime - lastActionTime < 1300){
        if(random(0,2)) left();
        else right();
      }
      else{
        lastActionTime = currentTime;
      }
    }
    else{
      forward();
    }
  }
}