import 'dart:async';

import '../ble/ble_manager.dart';
import '../ble/packet_parser.dart';
import '../storage/csv_writer.dart';

enum SessionState { idle, recording }

/// Coordinates a single gait-recording session: subscribes to IMU samples
/// from [BleManager] while recording and writes them to a CSV file via
/// [CsvWriter].
class SessionManager {
  final BleManager bleManager;

  SessionManager(this.bleManager);

  /// Accel magnitude (g) above or below 1g (resting) by this much counts
  /// as unusual motion — e.g. a stumble, fall, or sudden impact.
  static const double motionDeltaThresholdG = 1.5;

  /// Minimum gap between motion alerts, so a sustained shake doesn't fire
  /// continuously.
  static const Duration motionAlertCooldown = Duration(seconds: 2);

  final _stateController = StreamController<SessionState>.broadcast();
  final _sampleCountController = StreamController<int>.broadcast();
  final _latestSampleController = StreamController<ImuSample>.broadcast();
  final _motionAlertController = StreamController<ImuSample>.broadcast();

  StreamSubscription<ImuSample>? _sampleSubscription;
  CsvWriter? _csvWriter;
  int _sampleCount = 0;
  DateTime? _sessionStart;
  DateTime? _lastMotionAlert;

  Stream<SessionState> get state => _stateController.stream;
  Stream<int> get sampleCount => _sampleCountController.stream;
  Stream<ImuSample> get latestSample => _latestSampleController.stream;

  /// Fires whenever a sample's accel magnitude deviates from resting (1g)
  /// by more than [motionDeltaThresholdG], rate-limited by
  /// [motionAlertCooldown].
  Stream<ImuSample> get motionAlerts => _motionAlertController.stream;

  bool get isRecording => _csvWriter != null;

  /// Always emits live IMU samples for on-screen display, regardless of
  /// whether a recording session is active.
  void listenForLiveData() {
    _sampleSubscription ??= bleManager.imuSamples.listen((sample) {
      _latestSampleController.add(sample);
      _checkForUnusualMotion(sample);
      if (isRecording) {
        _csvWriter!.writeSample(sample);
        _sampleCount++;
        _sampleCountController.add(_sampleCount);
      }
    });
  }

  void _checkForUnusualMotion(ImuSample sample) {
    final delta = (sample.accelMagnitude - 1.0).abs();
    if (delta < motionDeltaThresholdG) return;

    final now = DateTime.now();
    if (_lastMotionAlert != null &&
        now.difference(_lastMotionAlert!) < motionAlertCooldown) {
      return;
    }
    _lastMotionAlert = now;
    _motionAlertController.add(sample);
  }

  Future<void> startSession({String? sessionName}) async {
    if (isRecording) return;
    _sessionStart = DateTime.now();
    final name = sessionName ?? _defaultSessionName(_sessionStart!);
    _csvWriter = await CsvWriter.create(name);
    _sampleCount = 0;
    _sampleCountController.add(0);
    listenForLiveData();
    _stateController.add(SessionState.recording);
  }

  Future<String?> stopSession() async {
    final writer = _csvWriter;
    if (writer == null) return null;
    _csvWriter = null;
    await writer.close();
    _stateController.add(SessionState.idle);
    return writer.file.path;
  }

  String _defaultSessionName(DateTime start) {
    String pad(int n, [int width = 2]) => n.toString().padLeft(width, '0');
    return 'session_${start.year}${pad(start.month)}${pad(start.day)}_'
        '${pad(start.hour)}${pad(start.minute)}${pad(start.second)}';
  }

  Future<void> dispose() async {
    await stopSession();
    await _sampleSubscription?.cancel();
    await _stateController.close();
    await _sampleCountController.close();
    await _latestSampleController.close();
    await _motionAlertController.close();
  }
}
