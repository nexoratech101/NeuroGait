import 'dart:async';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';

import 'packet_parser.dart';

/// GATT UUIDs exposed by firmware/nano33_imu_ble_firmware/nano33_imu_ble_firmware.ino.
/// Keep these in sync if the firmware UUIDs ever change.
class GaitBleUuids {
  static final Guid imuService =
      Guid('19b10000-e8f2-537e-4f6c-d104768a1214');
  static final Guid imuCharacteristic =
      Guid('19b10001-e8f2-537e-4f6c-d104768a1214');
}

enum BleConnectionState { disconnected, scanning, connecting, connected }

/// Owns BLE scanning, connecting, and IMU-notification streaming for a
/// single Nano 33 BLE gait-monitor device.
class BleManager {
  final _connectionStateController =
      StreamController<BleConnectionState>.broadcast();
  final _imuSampleController = StreamController<ImuSample>.broadcast();

  StreamSubscription<List<int>>? _notifySubscription;
  StreamSubscription<BluetoothConnectionState>? _deviceStateSubscription;

  BluetoothDevice? _device;

  Stream<BleConnectionState> get connectionState =>
      _connectionStateController.stream;
  Stream<ImuSample> get imuSamples => _imuSampleController.stream;
  Stream<List<ScanResult>> get scanResults => FlutterBluePlus.scanResults;

  bool get isConnected => _device != null;

  Future<void> startScan({Duration timeout = const Duration(seconds: 10)}) async {
    _connectionStateController.add(BleConnectionState.scanning);
    await FlutterBluePlus.startScan(
      withServices: [GaitBleUuids.imuService],
      timeout: timeout,
    );
  }

  Future<void> stopScan() async {
    await FlutterBluePlus.stopScan();
    if (_device == null) {
      _connectionStateController.add(BleConnectionState.disconnected);
    }
  }

  Future<void> connect(BluetoothDevice device) async {
    await stopScan();
    _connectionStateController.add(BleConnectionState.connecting);
    _device = device;

    _deviceStateSubscription?.cancel();
    _deviceStateSubscription = device.connectionState.listen((state) {
      if (state == BluetoothConnectionState.disconnected) {
        _connectionStateController.add(BleConnectionState.disconnected);
      }
    });

    await device.connect(autoConnect: false);
    await device.requestMtu(247);

    final services = await device.discoverServices();
    final service = services.firstWhere(
      (s) => s.uuid == GaitBleUuids.imuService,
      orElse: () => throw StateError(
        'IMU service ${GaitBleUuids.imuService} not found on device',
      ),
    );
    final characteristic = service.characteristics.firstWhere(
      (c) => c.uuid == GaitBleUuids.imuCharacteristic,
      orElse: () => throw StateError(
        'IMU characteristic ${GaitBleUuids.imuCharacteristic} not found',
      ),
    );
    await characteristic.setNotifyValue(true);
    _notifySubscription?.cancel();
    _notifySubscription = characteristic.onValueReceived.listen((bytes) {
      for (final sample in PacketParser.parse(bytes)) {
        _imuSampleController.add(sample);
      }
    });

    _connectionStateController.add(BleConnectionState.connected);
  }

  Future<void> disconnect() async {
    await _notifySubscription?.cancel();
    _notifySubscription = null;
    await _deviceStateSubscription?.cancel();
    _deviceStateSubscription = null;
    await _device?.disconnect();
    _device = null;
    _connectionStateController.add(BleConnectionState.disconnected);
  }

  Future<void> dispose() async {
    await disconnect();
    await _connectionStateController.close();
    await _imuSampleController.close();
  }
}
