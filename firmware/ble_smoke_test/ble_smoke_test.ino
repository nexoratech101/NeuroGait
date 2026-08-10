/*
 * BLE connectivity smoke test — NOT the real gait_app firmware.
 *
 * Advertises a generic service/characteristic and writes fixed test
 * strings. Use this with nRF Connect (or any generic BLE scanner) to
 * confirm the board's BLE radio advertises and accepts connections at
 * all, independent of the gait_app.
 *
 * This will NOT work with the gait_app Flutter app: it advertises a
 * different service UUID than GaitBleUuids.imuService in
 * lib/ble/ble_manager.dart, and sends plain strings instead of the
 * 28-byte binary packet PacketParser expects. For the real firmware,
 * flash firmware/nano33_imu_ble_firmware/nano33_imu_ble_firmware.ino.
 */

#include <ArduinoBLE.h>

BLEService gaitService("180C");
BLEStringCharacteristic dataChar("2A56", BLERead | BLENotify, 50);

void setup() {
  Serial.begin(115200);

  if (!BLE.begin()) {
    Serial.println("BLE failed!");
    while (1);
  }

  BLE.setLocalName("GaitIMU");
  BLE.setAdvertisedService(gaitService);

  gaitService.addCharacteristic(dataChar);
  BLE.addService(gaitService);

  dataChar.writeValue("Hello");

  BLE.advertise();
  Serial.println("BLE device is now advertising...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.println("Connected!");
    while (central.connected()) {
      dataChar.writeValue("123");
      delay(1000);
    }
    Serial.println("Disconnected");
  }
}
