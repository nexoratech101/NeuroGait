import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../ble/ble_manager.dart';
import '../ble/packet_parser.dart';
import '../session/session_manager.dart';

class SessionScreen extends StatefulWidget {
  final BleManager bleManager;

  const SessionScreen({super.key, required this.bleManager});

  @override
  State<SessionScreen> createState() => _SessionScreenState();
}

class _SessionScreenState extends State<SessionScreen> {
  late final SessionManager _sessionManager;
  ImuSample? _lastSample;
  int _sampleCount = 0;
  bool _isRecording = false;
  String? _lastSavedPath;

  @override
  void initState() {
    super.initState();
    _sessionManager = SessionManager(widget.bleManager)..listenForLiveData();
    _sessionManager.latestSample.listen((sample) {
      if (!mounted) return;
      setState(() => _lastSample = sample);
    });
    _sessionManager.sampleCount.listen((count) {
      if (!mounted) return;
      setState(() => _sampleCount = count);
    });
    _sessionManager.state.listen((state) {
      if (!mounted) return;
      setState(() => _isRecording = state == SessionState.recording);
    });
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      final path = await _sessionManager.stopSession();
      setState(() => _lastSavedPath = path);
    } else {
      setState(() => _lastSavedPath = null);
      await _sessionManager.startSession();
    }
  }

  @override
  void dispose() {
    _sessionManager.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final sample = _lastSample;
    return Scaffold(
      appBar: AppBar(title: const Text('Gait Session')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: sample == null
                    ? const Text('Waiting for IMU data...')
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('t = ${sample.timestampMs} ms'),
                          const SizedBox(height: 8),
                          Text('accel  x:${sample.accelX.toStringAsFixed(3)}  '
                              'y:${sample.accelY.toStringAsFixed(3)}  '
                              'z:${sample.accelZ.toStringAsFixed(3)}'),
                          Text('gyro   x:${sample.gyroX.toStringAsFixed(3)}  '
                              'y:${sample.gyroY.toStringAsFixed(3)}  '
                              'z:${sample.gyroZ.toStringAsFixed(3)}'),
                        ],
                      ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              _isRecording
                  ? 'Recording... $_sampleCount samples'
                  : 'Not recording',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _toggleRecording,
              icon: Icon(_isRecording ? Icons.stop : Icons.fiber_manual_record),
              label: Text(_isRecording ? 'Stop Session' : 'Start Session'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _isRecording ? Colors.red : null,
              ),
            ),
            if (_lastSavedPath != null) ...[
              const SizedBox(height: 16),
              Text('Saved to:\n$_lastSavedPath',
                  style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () =>
                    Share.shareXFiles([XFile(_lastSavedPath!)]),
                icon: const Icon(Icons.share),
                label: const Text('Share CSV'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
