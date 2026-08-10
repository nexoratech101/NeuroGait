import 'package:flutter/material.dart';

import 'ui/connect_screen.dart';

void main() {
  runApp(const GaitApp());
}

class GaitApp extends StatelessWidget {
  const GaitApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NeuroGait',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const ConnectScreen(),
    );
  }
}
