/*
   EV Power Monitoring - LoRa Receiver
   Board: Arduino UNO
*/

#include <SPI.h>
#include <LoRa.h>

// -------- LoRa Pins (UNO) --------
#define NSS 10
#define RST 9
#define DIO0 2

void setup() {
  Serial.begin(9600);

  // Required for UNO SPI
  pinMode(10, OUTPUT);
  digitalWrite(10, HIGH);

  LoRa.setPins(NSS, RST, DIO0);

  if (!LoRa.begin(433E6)) {
    while (1);   // Stop if LoRa fails
  }
}

void loop() {

  int packetSize = LoRa.parsePacket();

  if (packetSize) {

    String data = "";

    while (LoRa.available()) {
      data += (char)LoRa.read();
    }

    // IMPORTANT:
    // Send ONLY one clean line to Python
    Serial.println(data);
  }
}