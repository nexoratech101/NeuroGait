/*
 * Nano 33 BLE Rev2 — onboard IMU reader (accel + gyro only).
 * Prints readings to Serial Monitor at 115200 baud.
 *
 * Board: Arduino Nano 33 BLE / Nano 33 BLE Sense Rev2 (BMI270 + BMM150 IMU).
 * Library: Arduino_BMI270_BMM150 (install via Library Manager).
 */

#include <Arduino_BMI270_BMM150.h>

const unsigned long kSampleIntervalMs = 100; // 10 Hz
unsigned long lastSampleMs = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1) {
      delay(1000);
    }
  }

  Serial.print("Accelerometer sample rate: ");
  Serial.print(IMU.accelerationSampleRate());
  Serial.println(" Hz");
  Serial.print("Gyroscope sample rate: ");
  Serial.print(IMU.gyroscopeSampleRate());
  Serial.println(" Hz");

  Serial.println("accelX,accelY,accelZ,gyroX,gyroY,gyroZ");
}

void loop() {
  unsigned long now = millis();
  if (now - lastSampleMs < kSampleIntervalMs) {
    return;
  }

  if (!IMU.accelerationAvailable() || !IMU.gyroscopeAvailable()) {
    return;
  }

  float accelX, accelY, accelZ;
  float gyroX, gyroY, gyroZ;

  IMU.readAcceleration(accelX, accelY, accelZ);
  IMU.readGyroscope(gyroX, gyroY, gyroZ);

  Serial.print(accelX, 4);
  Serial.print(",");
  Serial.print(accelY, 4);
  Serial.print(",");
  Serial.print(accelZ, 4);
  Serial.print(",");
  Serial.print(gyroX, 4);
  Serial.print(",");
  Serial.print(gyroY, 4);
  Serial.print(",");
  Serial.println(gyroZ, 4);

  lastSampleMs = now;
}
