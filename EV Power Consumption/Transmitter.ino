/*
  OBU Transmitter - EV Power Minimization Project
  Hardware: Arduino Mega 2560, LoRa RFM95W, INA219, MPU6050, DHT11, GPS
  Display: 16x2 LCD with I2C Backpack
*/

#include <Adafruit_INA219.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h> // Library for I2C LCD
#include <LoRa.h>
#include <SPI.h>
#include <TinyGPS++.h>
#include <Wire.h>


// --- Configuration ---
// LCD Address is usually 0x27 or 0x3F. Run an I2C Scanner if it doesn't work.
LiquidCrystal_I2C lcd(0x27, 16, 2);

// LoRa Pins (Arduino Mega)
#define NSS_PIN 53
#define RST_PIN 9
#define DIO0_PIN 2

// DHT11
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// GPS
TinyGPSPlus gps;
#define GPSSerial Serial1

// Power Sensor
Adafruit_INA219 ina219;

// IMU
Adafruit_MPU6050 mpu;

unsigned long lastSendTime = 0;
const int interval = 2000; // Send every 2 seconds

void setup() {
  Serial.begin(115200);
  GPSSerial.begin(9600);

  // --- Init LCD ---
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("EV Power Monitor");
  lcd.setCursor(0, 1);
  lcd.print("Initializing...");
  delay(1000);

  // --- Init INA219 ---
  if (!ina219.begin()) {
    Serial.println("Failed to find INA219 chip");
    lcd.clear();
    lcd.print("INA219 Error");
  }

  // --- Init MPU6050 ---
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    lcd.setCursor(0, 1);
    lcd.print("MPU6050 Error");
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  // --- Init DHT ---
  dht.begin();

  // --- Init LoRa ---
  LoRa.setPins(NSS_PIN, RST_PIN, DIO0_PIN);
  if (!LoRa.begin(433E6)) {
    Serial.println("Starting LoRa failed!");
    lcd.clear();
    lcd.print("LoRa Error");
    while (1)
      ;
  }

  lcd.clear();
  lcd.print("System Ready");
  delay(1000);
}

void loop() {
  // Feed GPS
  while (GPSSerial.available() > 0) {
    gps.encode(GPSSerial.read());
  }

  if (millis() - lastSendTime > interval) {
    // Read Sensors
    float voltage = ina219.getBusVoltage_V();
    float current_mA = ina219.getCurrent_mA();
    float power_mW = ina219.getPower_mW();
    float temp = dht.readTemperature();

    // Read IMU
    sensors_event_t a, g, temp_imu;
    mpu.getEvent(&a, &g, &temp_imu);

    // Read GPS
    double lat = 0.0, lng = 0.0;
    if (gps.location.isValid()) {
      lat = gps.location.lat();
      lng = gps.location.lng();
    }

    // Format Data Bundle
    String data = "";
    data += "V:" + String(voltage, 2) + ",";
    data += "C:" + String(current_mA, 1) + ",";
    data += "P:" + String(power_mW, 1) + ",";
    data += "T:" + String(temp, 1) + ",";
    data += "A:" + String(a.acceleration.x, 2) + ",";
    data += "La:" + String(lat, 6) + ",";
    data += "Ln:" + String(lng, 6);

    // Send LoRa Packet
    LoRa.beginPacket();
    LoRa.print(data);
    LoRa.endPacket();

    Serial.println("Sent: " + data);

    // Update LCD
    lcd.clear();
    // Line 1: Voltage and Current
    lcd.setCursor(0, 0);
    lcd.print("V:");
    lcd.print(voltage, 1);
    lcd.print(" I:");
    lcd.print(current_mA, 0);

    // Line 2: Power and Temp
    lcd.setCursor(0, 1);
    lcd.print("P:");
    lcd.print(power_mW, 0);
    lcd.print(" T:");
    lcd.print(temp, 0);

    lastSendTime = millis();
  }
}