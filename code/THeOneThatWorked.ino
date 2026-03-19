const int ldrPin = A1;   // Photoresistor
const int ledPin = 5;    // MUST be PWM pin (3,5,6,9,10,11)

// Your real measured values
const int brightValue = 900;   // very bright
const int darkStart = 400;     // LED starts turning on
const int veryDark = 100;      // max brightness

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int ldrValue = analogRead(ldrPin);
  int brightness = 0;

  // Case 1: Very bright → LED OFF
  if (ldrValue >= darkStart) {
    brightness = 0;
  }

  // Case 2: Medium light → gradually increase brightness
  else if (ldrValue < darkStart && ldrValue > veryDark) {
    brightness = map(ldrValue, darkStart, veryDark, 0, 255);
  }

  // Case 3: Very dark → MAX brightness
  else if (ldrValue <= veryDark) {
    brightness = 255;
  }

  analogWrite(ledPin, brightness);

  // Debugging output
  Serial.print("LDR: ");
  Serial.print(ldrValue);
  Serial.print("  Brightness: ");
  Serial.println(brightness);

  delay(100);
}