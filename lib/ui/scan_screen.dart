import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

import '../ble/ble_manager.dart';
import 'session_screen.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final BleManager _bleManager = BleManager();
  List<ScanResult> _results = [];
  bool _isScanning = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _bleManager.scanResults.listen((results) {
      if (!mounted) return;
      setState(() {
        _results = results.where((r) => r.device.platformName.isNotEmpty).toList();
      });
    });
    FlutterBluePlus.isScanning.listen((scanning) {
      if (!mounted) return;
      setState(() => _isScanning = scanning);
    });
  }

  Future<void> _startScan() async {
    setState(() => _error = null);
    final granted = await _requestPermissions();
    if (!granted) {
      setState(() => _error = 'Bluetooth/location permissions are required to scan.');
      return;
    }
    try {
      await _bleManager.startScan();
    } catch (e) {
      setState(() => _error = 'Scan failed: $e');
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

  Future<void> _connect(ScanResult result) async {
    try {
      await _bleManager.connect(result.device);
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => SessionScreen(bleManager: _bleManager),
        ),
      );
    } catch (e) {
      setState(() => _error = 'Connect failed: $e');
    }
  }

  @override
  void dispose() {
    _bleManager.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('NeuroGait — Find Device')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _isScanning ? _bleManager.stopScan : _startScan,
        icon: Icon(_isScanning ? Icons.stop : Icons.search),
        label: Text(_isScanning ? 'Stop Scan' : 'Scan'),
      ),
      body: Column(
        children: [
          if (_error != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Text(_error!, style: const TextStyle(color: Colors.red)),
            ),
          Expanded(
            child: _results.isEmpty
                ? Center(
                    child: Text(_isScanning
                        ? 'Scanning for gait-monitor devices...'
                        : 'Tap Scan to find your Nano 33 BLE device'),
                  )
                : ListView.builder(
                    itemCount: _results.length,
                    itemBuilder: (context, index) {
                      final result = _results[index];
                      return ListTile(
                        title: Text(result.device.platformName),
                        subtitle: Text(result.device.remoteId.str),
                        trailing: Text('${result.rssi} dBm'),
                        onTap: () => _connect(result),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
