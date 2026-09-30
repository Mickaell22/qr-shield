import 'package:flutter/material.dart';

import 'analysis_page.dart';
import 'config.dart';
import 'content.dart';
import 'motor_client.dart';

class HomePage extends StatefulWidget {
  /// Nulo si la app se compilo sin `MOTOR_URL`.
  final MotorClient? client;
  const HomePage({super.key, required this.client});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _url = TextEditingController();

  @override
  void dispose() {
    _url.dispose();
    super.dispose();
  }

  void _submit(MotorClient client) {
    switch (classify(_url.text)) {
      case NotLinkContent(:final kind):
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(
            SnackBar(content: Text('El contenido es $kind, no un enlace.')),
          );
      case LinkContent(:final url):
        Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) => AnalysisPage(client: client, url: url),
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final client = widget.client;
    return Scaffold(
      appBar: AppBar(title: const Text(productName)),
      body: client == null
          ? const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'La app se compiló sin la dirección del motor (MOTOR_URL).',
                  textAlign: TextAlign.center,
                ),
              ),
            )
          : ListView(
              padding: const EdgeInsets.all(24),
              children: [
                TextField(
                  controller: _url,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  textInputAction: TextInputAction.go,
                  onSubmitted: (_) => _submit(client),
                  decoration: const InputDecoration(
                    labelText: 'Enlace a analizar',
                    hintText: 'https://ejemplo.com',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: () => _submit(client),
                  icon: const Icon(Icons.search),
                  label: const Text('Analizar'),
                ),
              ],
            ),
    );
  }
}
