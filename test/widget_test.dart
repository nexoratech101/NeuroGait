import 'package:flutter_test/flutter_test.dart';

import 'package:gait_app/main.dart';

void main() {
  testWidgets('App launches to the scan screen', (WidgetTester tester) async {
    await tester.pumpWidget(const GaitApp());

    expect(find.text('NeuroGait — Find Device'), findsOneWidget);
    expect(find.text('Scan'), findsOneWidget);
  });
}
