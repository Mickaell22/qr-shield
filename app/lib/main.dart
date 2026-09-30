import 'package:flutter/material.dart';

import 'config.dart';

void main() => runApp(const App());

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: productName,
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: Scaffold(
        appBar: AppBar(title: const Text(productName)),
        body: Center(
          child: Text(
            motorUrl.isEmpty
                ? 'Falta configurar MOTOR_URL al compilar.'
                : 'Motor: $motorUrl',
          ),
        ),
      ),
    );
  }
}
