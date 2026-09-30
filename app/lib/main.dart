import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'config.dart';
import 'home_page.dart';
import 'motor_client.dart';

void main() => runApp(
  App(client: motorUrl.isEmpty ? null : MotorClient(http.Client(), motorUrl)),
);

class App extends StatelessWidget {
  final MotorClient? client;
  const App({super.key, required this.client});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: productName,
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: HomePage(client: client),
    );
  }
}
