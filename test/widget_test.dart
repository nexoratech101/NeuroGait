import 'package:flutter_test/flutter_test.dart';

import 'package:gait_app/main.dart';

void main() {
  testWidgets('App launches to an idle screen with a Connect button',
      (WidgetTester tester) async {
    await tester.pumpWidget(const GaitApp());

    expect(find.text('NeuroGait'), findsOneWidget);
    expect(find.text('Connect'), findsOneWidget);
  });
}
