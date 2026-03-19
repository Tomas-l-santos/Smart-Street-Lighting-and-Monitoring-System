// LED TEST - PINS 1 TO 13

void setup() {
  // Set pins 1 to 13 as OUTPUT
  for (int pin = 1; pin <= 13; pin++) {
    pinMode(pin, OUTPUT);
  }
}

void loop() {
  // Turn ON each LED one by one
  for (int pin = 1; pin <= 13; pin++) {
    digitalWrite(pin, HIGH);   // LED ON
    delay(500);                // wait 0.5 sec
    digitalWrite(pin, LOW);    // LED OFF
  }
}