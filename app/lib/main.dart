import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'config.dart';
import 'home_page.dart';
import 'motor_client.dart';
import 'scanner_page.dart';

void main() => runApp(
  App(client: motorUrl.isEmpty ? null : MotorClient(http.Client(), motorUrl)),
);

class App extends StatelessWidget {
  final MotorClient? client;
  final Future<String?> Function(BuildContext) scan;
  const App({super.key, required this.client, this.scan = scanQr});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: productName,
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: HomePage(client: client, scan: scan),
    );
  }
}
