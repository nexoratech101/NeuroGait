import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:vibration/vibration.dart';

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
  static const int _chartBufferMaxLength = 100;
  static const double _chartMaxG = 4.0;

  late final SessionManager _sessionManager;
  final List<ImuSample> _chartBuffer = [];
  ImuSample? _lastSample;
  int _sampleCount = 0;
  bool _isRecording = false;
  bool _hasVibrator = false;
  bool _showMotionAlert = false;
  String? _lastSavedPath;

  @override
  void initState() {
    super.initState();
    _sessionManager = SessionManager(widget.bleManager)..listenForLiveData();

    Vibration.hasVibrator().then((has) {
      _hasVibrator = has == true;
    });

    _sessionManager.latestSample.listen((sample) {
      if (!mounted) return;
      setState(() {
        _lastSample = sample;
        _chartBuffer.add(sample);
        if (_chartBuffer.length > _chartBufferMaxLength) {
          _chartBuffer.removeAt(0);
        }
      });
    });
    _sessionManager.sampleCount.listen((count) {
      if (!mounted) return;
      setState(() => _sampleCount = count);
    });
    _sessionManager.state.listen((state) {
      if (!mounted) return;
      setState(() => _isRecording = state == SessionState.recording);
    });
    _sessionManager.motionAlerts.listen((sample) {
      if (_hasVibrator) {
        Vibration.vibrate(duration: 400);
      }
      if (!mounted) return;
      setState(() => _showMotionAlert = true);
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) setState(() => _showMotionAlert = false);
      });
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

  Widget _buildChart() {
    if (_chartBuffer.isEmpty) {
      return const Center(child: Text('Waiting for IMU data...'));
    }
    final spots = [
      for (var i = 0; i < _chartBuffer.length; i++)
        FlSpot(i.toDouble(), _chartBuffer[i].accelMagnitude),
    ];
    return LineChart(
      duration: Duration.zero,
      LineChartData(
        minY: 0,
        maxY: _chartMaxG,
        titlesData: const FlTitlesData(show: false),
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        borderData: FlBorderData(show: false),
        lineTouchData: const LineTouchData(enabled: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: false,
            color: Colors.teal,
            barWidth: 2,
            dotData: const FlDotData(show: false),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final sample = _lastSample;
    return Scaffold(
      appBar: AppBar(title: const Text('Gait Session')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_showMotionAlert)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.warning_amber_rounded, color: Colors.red),
                    SizedBox(width: 8),
                    Text('Unusual motion detected!',
                        style: TextStyle(
                            color: Colors.red, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
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
            Card(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(8, 12, 16, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Padding(
                      padding: EdgeInsets.only(left: 8),
                      child: Text('Accel magnitude (g)'),
                    ),
                    SizedBox(height: 160, child: _buildChart()),
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
