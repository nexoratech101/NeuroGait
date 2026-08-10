import 'dart:typed_data';

/// One IMU sample streamed from the Nano 33 BLE firmware.
///
/// Wire format (little-endian, 28 bytes total) — must stay in sync with
/// the packet struct in firmware/nano33_imu_ble_firmware/nano33_imu_ble_firmware.ino:
///   uint32  timestampMs   (offset 0)
///   float32 accelX        (offset 4)
///   float32 accelY        (offset 8)
///   float32 accelZ        (offset 12)
///   float32 gyroX         (offset 16)
///   float32 gyroY         (offset 20)
///   float32 gyroZ         (offset 24)
class ImuSample {
  static const int packetLengthBytes = 28;

  final int timestampMs;
  final double accelX;
  final double accelY;
  final double accelZ;
  final double gyroX;
  final double gyroY;
  final double gyroZ;

  const ImuSample({
    required this.timestampMs,
    required this.accelX,
    required this.accelY,
    required this.accelZ,
    required this.gyroX,
    required this.gyroY,
    required this.gyroZ,
  });

  List<Object> toCsvRow() => [
        timestampMs,
        accelX,
        accelY,
        accelZ,
        gyroX,
        gyroY,
        gyroZ,
      ];

  static const List<String> csvHeader = [
    'timestamp_ms',
    'accel_x',
    'accel_y',
    'accel_z',
    'gyro_x',
    'gyro_y',
    'gyro_z',
  ];

  @override
  String toString() =>
      'ImuSample(t=$timestampMs, a=($accelX, $accelY, $accelZ), '
      'g=($gyroX, $gyroY, $gyroZ))';
}

/// Parses raw BLE notification bytes into [ImuSample]s.
///
/// A single BLE notification may contain more than one packet back-to-back
/// once MTU negotiation succeeds, so [parse] returns a list.
class PacketParser {
  static List<ImuSample> parse(List<int> rawBytes) {
    final samples = <ImuSample>[];
    final bytes = Uint8List.fromList(rawBytes);
    final byteData = ByteData.sublistView(bytes);

    final usableLength =
        bytes.length - (bytes.length % ImuSample.packetLengthBytes);
    for (var offset = 0; offset < usableLength;
        offset += ImuSample.packetLengthBytes) {
      samples.add(
        ImuSample(
          timestampMs: byteData.getUint32(offset, Endian.little),
          accelX: byteData.getFloat32(offset + 4, Endian.little),
          accelY: byteData.getFloat32(offset + 8, Endian.little),
          accelZ: byteData.getFloat32(offset + 12, Endian.little),
          gyroX: byteData.getFloat32(offset + 16, Endian.little),
          gyroY: byteData.getFloat32(offset + 20, Endian.little),
          gyroZ: byteData.getFloat32(offset + 24, Endian.little),
        ),
      );
    }
    return samples;
  }
}
