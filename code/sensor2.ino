// ============================================================
//  Arduino Uno — LED + Photoresistor (LDR) Sensor Node
//  Sends JSON over Serial at 9600 baud every 500 ms
//
//  Wiring:
//    LDR one leg       → 5V
//    LDR other leg     → A0  AND  10kΩ resistor to GND
//    (voltage divider: 5V → LDR → A0 → 10kΩ → GND)
//
//    LED anode  → 220Ω → D7
//    LED cathode → GND
// ============================================================

const int LDR_PIN   = A0;   // Photoresistor middle of voltage divider
const int LED_PIN   = 13;   // Onboard LED — power indicator (stays ON)
const int BLINK_PIN = 7;    // External LED — blinks each reading

const float VCC         = 5.0;
const float R_FIXED     = 10000.0;  // 10kΩ pull-down resistor value

unsigned long lastSend = 0;
const unsigned long INTERVAL = 500;  // ms between readings

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN,   OUTPUT);
  pinMode(BLINK_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);  // Keep power indicator on
}

void loop() {
  unsigned long now = millis();

  if (now - lastSend >= INTERVAL) {
    lastSend = now;

    int   raw     = analogRead(LDR_PIN);              // 0–1023
    float voltage = raw * (VCC / 1023.0);             // Voltage at A0

    // Calculate LDR resistance from voltage divider formula:
    // V_out = VCC * R_FIXED / (R_LDR + R_FIXED)
    // R_LDR = R_FIXED * (VCC - V_out) / V_out
    float ldrResistance = 0;
    if (voltage > 0.01) {  // Avoid divide-by-zero in complete darkness
      ldrResistance = R_FIXED * (VCC - voltage) / voltage;
    } else {
      ldrResistance = 999999;  // Effectively infinite (full dark)
    }

    // Convert resistance to lux using common LDR empirical formula:
    // lux ≈ 500 / (R_LDR / 1000)   — works for typical GL5528 LDR
    // Higher resistance = less light = fewer lux
    float lux = 0;
    if (ldrResistance > 0) {
      lux = 500.0 / (ldrResistance / 1000.0);
    }
    lux = constrain(lux, 0, 10000);  // Cap at 10,000 lux

    // Blink external LED to show activity
    digitalWrite(BLINK_PIN, !digitalRead(BLINK_PIN));

    // Emit JSON — parsed by the Python dashboard
    Serial.print("{\"raw\":");
    Serial.print(raw);
    Serial.print(",\"voltage\":");
    Serial.print(voltage, 3);
    Serial.print(",\"ldr_ohms\":");
    Serial.print(ldrResistance, 0);
    Serial.print(",\"lux\":");
    Serial.print(lux, 1);
    Serial.print(",\"uptime\":");
    Serial.print(now);
    Serial.println("}");
  }
}
