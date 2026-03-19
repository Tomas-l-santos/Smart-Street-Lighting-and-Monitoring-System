// PHOTORESISTOR TEST (LDR on A1)

int ldrPin = A1;
int ldrValue = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  ldrValue = analogRead(ldrPin);

  Serial.print("Light Value: ");
  Serial.println(ldrValue);

  delay(500);
}