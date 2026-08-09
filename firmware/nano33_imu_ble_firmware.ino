/*
 * NeuroGait — Nano 33 BLE Sense IMU streamer.
 *
 * Streams accelerometer + gyroscope samples over BLE notify as fixed-size
 * 28-byte binary packets. The layout below MUST stay in sync with
 * ImuSample / PacketParser in lib/ble/packet_parser.dart:
 *
 *   offset  0: uint32_t timestampMs   (millis() since boot, little-endian)
 *   offset  4: float    accelX        (g)
 *   offset  8: float    accelY        (g)
 *   offset 12: float    accelZ        (g)
 *   offset 16: float    gyroX         (deg/s)
 *   offset 20: float    gyroY         (deg/s)
 *   offset 24: float    gyroZ         (deg/s)
 *
 * Board: Arduino Nano 33 BLE Sense (rev1, LSM9DS1 IMU).
 * Libraries: ArduinoBLE, Arduino_LSM9DS1.
 */

#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>

// Must match GaitBleUuids in lib/ble/ble_manager.dart.
BLEService imuService("19b10000-e8f2-537e-4f6c-d104768a1214");
BLECharacteristic imuCharacteristic(
    "19b10001-e8f2-537e-4f6c-d104768a1214",
    BLERead | BLENotify,
    28);

const unsigned long kSampleIntervalMs = 20; // ~50 Hz
unsigned long lastSampleMs = 0;

struct __attribute__((packed)) ImuPacket {
  uint32_t timestampMs;
  float accelX;
  float accelY;
  float accelZ;
  float gyroX;
  float gyroY;
  float gyroZ;
};

static_assert(sizeof(ImuPacket) == 28, "ImuPacket must stay 28 bytes");

void setup() {
  Serial.begin(115200);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1) {
      delay(1000);
    }
  }

  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    while (1) {
      delay(1000);
    }
  }

  BLE.setLocalName("NeuroGait-IMU");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuCharacteristic);
  BLE.addService(imuService);

  BLE.advertise();
  Serial.println("BLE advertising as NeuroGait-IMU");
}

void loop() {
  BLEDevice central = BLE.central();
  if (!central) {
    return;
  }

  Serial.print("Connected to central: ");
  Serial.println(central.address());

  while (central.connected()) {
    unsigned long now = millis();
    if (now - lastSampleMs < kSampleIntervalMs) {
      continue;
    }

    if (!IMU.accelerationAvailable() || !IMU.gyroscopeAvailable()) {
      continue;
    }

    ImuPacket packet;
    packet.timestampMs = now;
    IMU.readAcceleration(packet.accelX, packet.accelY, packet.accelZ);
    IMU.readGyroscope(packet.gyroX, packet.gyroY, packet.gyroZ);

    imuCharacteristic.writeValue(reinterpret_cast<uint8_t*>(&packet), sizeof(packet));
    lastSampleMs = now;
  }

  Serial.print("Disconnected from central: ");
  Serial.println(central.address());
}
