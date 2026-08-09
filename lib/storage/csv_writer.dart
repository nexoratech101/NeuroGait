import 'dart:io';

import 'package:path_provider/path_provider.dart';

import '../ble/packet_parser.dart';

/// Writes IMU samples for one recording session to a CSV file under the
/// app's documents directory, one row per sample, flushed incrementally.
class CsvWriter {
  final IOSink _sink;
  final File file;

  CsvWriter._(this.file, this._sink);

  static Future<CsvWriter> create(String sessionName) async {
    final dir = await getApplicationDocumentsDirectory();
    final sessionsDir = Directory('${dir.path}/gait_sessions');
    if (!await sessionsDir.exists()) {
      await sessionsDir.create(recursive: true);
    }
    final file = File('${sessionsDir.path}/$sessionName.csv');
    final sink = file.openWrite();
    sink.writeln(ImuSample.csvHeader.join(','));
    return CsvWriter._(file, sink);
  }

  void writeSample(ImuSample sample) {
    _sink.writeln(sample.toCsvRow().join(','));
  }

  Future<void> close() async {
    await _sink.flush();
    await _sink.close();
  }
}
