// This is to test if the photo Diode works // 

const int sensorPin = A1;  // Your photodiode / LDR pin

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(sensorPin);

  Serial.print("Sensor Value: ");
  Serial.println(sensorValue);

  delay(500);
}