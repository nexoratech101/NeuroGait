import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

import '../ble/ble_manager.dart';
import 'session_screen.dart';

enum _ConnectStatus { idle, requestingPermissions, searching, connecting, failed }

/// Automatically finds and connects to the single expected NeuroGait-IMU
/// device (there's only ever one on a session), then hands off to
/// [SessionScreen]. No device picker — nothing else to choose between.
class ConnectScreen extends StatefulWidget {
  const ConnectScreen({super.key});

  @override
  State<ConnectScreen> createState() => _ConnectScreenState();
}

class _ConnectScreenState extends State<ConnectScreen> {
  final BleManager _bleManager = BleManager();
  StreamSubscription<List<ScanResult>>? _scanSubscription;
  _ConnectStatus _status = _ConnectStatus.idle;
  String? _error;

  Future<void> _start() async {
    setState(() {
      _status = _ConnectStatus.requestingPermissions;
      _error = null;
    });

    final granted = await _requestPermissions();
    if (!granted) {
      setState(() {
        _status = _ConnectStatus.failed;
        _error = 'Bluetooth/location permissions are required to connect.';
      });
      return;
    }

    setState(() => _status = _ConnectStatus.searching);

    var connecting = false;
    _scanSubscription?.cancel();
    _scanSubscription = _bleManager.scanResults.listen((results) async {
      if (connecting || results.isEmpty) return;
      connecting = true;
      await _bleManager.stopScan();
      await _connect(results.first.device);
    });

    try {
      await _bleManager.startScan(timeout: const Duration(seconds: 30));
    } catch (e) {
      setState(() {
        _status = _ConnectStatus.failed;
        _error = 'Scan failed: $e';
      });
    }
  }

  Future<bool> _requestPermissions() async {
    final statuses = await [
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.locationWhenInUse,
    ].request();
    return statuses.values.every((s) => s.isGranted || s.isLimited);
  }

  Future<void> _connect(BluetoothDevice device) async {
    setState(() => _status = _ConnectStatus.connecting);
    try {
      await _bleManager.connect(device);
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => SessionScreen(bleManager: _bleManager),
        ),
      );
    } catch (e) {
      setState(() {
        _status = _ConnectStatus.failed;
        _error = 'Connect failed: $e';
      });
    }
  }

  @override
  void dispose() {
    _scanSubscription?.cancel();
    if (_status != _ConnectStatus.connecting) {
      _bleManager.dispose();
    }
    super.dispose();
  }

  String get _statusText {
    switch (_status) {
      case _ConnectStatus.idle:
        return 'Ready to connect to your NeuroGait-IMU device.';
      case _ConnectStatus.requestingPermissions:
        return 'Requesting Bluetooth permissions...';
      case _ConnectStatus.searching:
        return 'Searching for NeuroGait-IMU...';
      case _ConnectStatus.connecting:
        return 'Connecting...';
      case _ConnectStatus.failed:
        return _error ?? 'Something went wrong.';
    }
  }

  @override
  Widget build(BuildContext context) {
    final failed = _status == _ConnectStatus.failed;
    final idle = _status == _ConnectStatus.idle;
    final busy = !failed && !idle;
    return Scaffold(
      appBar: AppBar(title: const Text('NeuroGait')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (busy) const CircularProgressIndicator(),
              if (idle) const Icon(Icons.bluetooth, size: 64),
              const SizedBox(height: 24),
              Text(
                _statusText,
                textAlign: TextAlign.center,
                style: failed
                    ? const TextStyle(color: Colors.red)
                    : Theme.of(context).textTheme.titleMedium,
              ),
              if (idle) ...[
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: _start,
                  icon: const Icon(Icons.bluetooth_searching),
                  label: const Text('Connect'),
                ),
              ],
              if (failed) ...[
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: _start,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
