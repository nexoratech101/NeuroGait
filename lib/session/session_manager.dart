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

  final _stateController = StreamController<SessionState>.broadcast();
  final _sampleCountController = StreamController<int>.broadcast();
  final _latestSampleController = StreamController<ImuSample>.broadcast();

  StreamSubscription<ImuSample>? _sampleSubscription;
  CsvWriter? _csvWriter;
  int _sampleCount = 0;
  DateTime? _sessionStart;

  Stream<SessionState> get state => _stateController.stream;
  Stream<int> get sampleCount => _sampleCountController.stream;
  Stream<ImuSample> get latestSample => _latestSampleController.stream;

  bool get isRecording => _csvWriter != null;

  /// Always emits live IMU samples for on-screen display, regardless of
  /// whether a recording session is active.
  void listenForLiveData() {
    _sampleSubscription ??= bleManager.imuSamples.listen((sample) {
      _latestSampleController.add(sample);
      if (isRecording) {
        _csvWriter!.writeSample(sample);
        _sampleCount++;
        _sampleCountController.add(_sampleCount);
      }
    });
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
  }
}
