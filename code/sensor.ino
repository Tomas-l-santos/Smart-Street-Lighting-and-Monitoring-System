// ============================================================
//  Arduino Uno — LED + Photodiode Sensor Node
//  Sends JSON over Serial at 9600 baud every 500 ms
// ============================================================

const int PHOTO_PIN  = A0;   // Photodiode to A0 (with pull-down resistor)
const int LED_PIN    = 13;   // Onboard LED (or external on D13)
const int BLINK_PIN  = 7;    // External LED for blink-test (optional)

unsigned long lastSend = 0;
const unsigned long INTERVAL = 500; // ms between readings

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN,   OUTPUT);
  pinMode(BLINK_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);   // keep indicator LED on
}

void loop() {
  unsigned long now = millis();

  if (now - lastSend >= INTERVAL) {
    lastSend = now;

    int raw       = analogRead(PHOTO_PIN);          // 0–1023
    float voltage = raw * (5.0 / 1023.0);           // 0–5 V
    float lux     = mapToLux(raw);                  // rough lux estimate

    // Toggle blink LED so the dashboard can show activity
    digitalWrite(BLINK_PIN, !digitalRead(BLINK_PIN));

    // Emit compact JSON — easy to parse in Python
    Serial.print("{\"raw\":");
    Serial.print(raw);
    Serial.print(",\"voltage\":");
    Serial.print(voltage, 3);
    Serial.print(",\"lux\":");
    Serial.print(lux, 1);
    Serial.print(",\"uptime\":");
    Serial.print(now);
    Serial.println("}");
  }
}

// Very rough linear lux approximation for a generic photodiode
// Calibrate the multiplier for your specific component datasheet
float mapToLux(int raw) {
  return raw * 0.9775;   // ≈ 0–1000 lux across 0–1023
}
