#include <Arduino.h>
#include <TM1637Display.h>  // 4-Digit Display Library

// TM1637 pins
#define CLK 2
#define DIO 15

// ESP32-CAM built-in LED (used only for emergency blink)
#define ESP32_CAM_LED 33

// TM1637 display object
TM1637Display display(CLK, DIO);

// Serial input
String receivedData = "";
int countdown = 0;
bool emergencyMode = false;

void setup() {
  Serial.begin(115200);

  // Initialize display and ESP32-CAM LED
  display.setBrightness(7);
  display.showNumberDec(0, true);  // Show "0000" at start

  pinMode(ESP32_CAM_LED, OUTPUT);
  digitalWrite(ESP32_CAM_LED, LOW);

  Serial.println("📟 Display + Emergency Mode Ready");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      // Handle emergency signals
      if (receivedData.startsWith("E")) {
        emergencyMode = true;
        Serial.println("🚨 Emergency Mode ON");
        receivedData = "";
        return;
      } else if (receivedData.startsWith("N")) {
        emergencyMode = false;
        Serial.println("✅ Emergency Mode OFF");
        digitalWrite(ESP32_CAM_LED, LOW); // Stop blinking if off
        receivedData = "";
        return;
      }

      // Handle normal countdown
      countdown = receivedData.toInt();
      receivedData = "";

      display.showNumberDec(countdown, true);  // Update display
      Serial.print("⏳ Countdown: ");
      Serial.println(countdown);
    } else {
      receivedData += c;
    }
  }

  // Emergency blinking mode
  if (emergencyMode) {
    digitalWrite(ESP32_CAM_LED, HIGH);
    delay(300);
    digitalWrite(ESP32_CAM_LED, LOW);
    delay(300);
  }
}
