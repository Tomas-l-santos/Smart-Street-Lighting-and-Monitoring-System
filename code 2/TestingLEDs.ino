void setup() {
  Serial.begin(9600);

  // Set all pins 2–13 as OUTPUT
  for (int pin = 2; pin <= 13; pin++) {
    pinMode(pin, OUTPUT);
  }

  Serial.println("=== FULL PIN SCAN START ===");
}

void loop() {

  for (int pin = 2; pin <= 13; pin++) {

    Serial.print("Testing pin: ");
    Serial.println(pin);

    // Turn ON current pin
    digitalWrite(pin, HIGH);

    delay(1000); // Enough time to clearly see

    // Turn OFF
    digitalWrite(pin, LOW);

    delay(300);
  }

  Serial.println("---- Scan Complete ----");
  delay(2000);
}