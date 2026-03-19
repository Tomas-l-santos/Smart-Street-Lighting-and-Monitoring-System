const int sensorPin = A1;

// Small LEDs
const int LED1 = 13;
const int LED2 = 2;
const int LED3 = 3;
const int LED4 = 4;
const int LED5 = 5;
const int LED6 = 6;

// Big LED
const int BIGLED = 7;

int sensorValue = 0;

void setup() {
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  pinMode(LED4, OUTPUT);
  pinMode(LED5, OUTPUT);
  pinMode(LED6, OUTPUT);
  pinMode(BIGLED, OUTPUT);

  Serial.begin(9600);
}

void loop() {
  sensorValue = analogRead(sensorPin);

  Serial.print("Sensor Value: ");
  Serial.println(sensorValue);

  // Turn everything ON first
  digitalWrite(LED1, HIGH);
  digitalWrite(LED2, HIGH);
  digitalWrite(LED3, HIGH);
  digitalWrite(LED4, HIGH);
  digitalWrite(LED5, HIGH);
  digitalWrite(LED6, HIGH);
  digitalWrite(BIGLED, HIGH);

  // --- BIG LED (only ON when dark) ---
  if (sensorValue <= 500) {
    digitalWrite(BIGLED, LOW);
  }

  // --- SMALL LEDs (light meter reversed) ---
  
  if (sensorValue > 800) {
    // Very bright → all OFF
  }
  else if (sensorValue > 650) {
    // Slightly bright → 1 LED ON
    digitalWrite(LED1, LOW);
  }
  else if (sensorValue > 500) {
    // Medium → 2 LEDs ON
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
  }
  else if (sensorValue > 350) {
    // Getting darker → 3 LEDs ON
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);
  }
  else if (sensorValue > 250) {
    // Dark → 4 LEDs ON
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);
    digitalWrite(LED4, LOW);
  }
  else if (sensorValue > 150) {
    // Very dark → 5 LEDs ON
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);
    digitalWrite(LED4, LOW);
    digitalWrite(LED5, LOW);
  }
  else {
    // Extremely dark → all 6 LEDs ON
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);
    digitalWrite(LED4, LOW);
    digitalWrite(LED5, LOW);
    digitalWrite(LED6, LOW);
  }

  delay(200);
}