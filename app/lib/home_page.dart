import 'package:flutter/material.dart';

import 'analysis_page.dart';
import 'config.dart';
import 'content.dart';
import 'motor_client.dart';
import 'scanner_page.dart';

class HomePage extends StatefulWidget {
  /// Nulo si la app se compilo sin `MOTOR_URL`.
  final MotorClient? client;

  /// Abre el escaner y devuelve lo leido. Inyectable para testear sin camara.
  final Future<String?> Function(BuildContext) scan;
  const HomePage({super.key, required this.client, this.scan = scanQr});

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

  Future<void> _scan(MotorClient client) async {
    final text = await widget.scan(context);
    if (text != null && mounted) _handle(client, text);
  }

  // Lo escaneado y lo escrito a mano siguen el mismo camino.
  void _handle(MotorClient client, String text) {
    switch (classify(text)) {
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
                FilledButton.icon(
                  onPressed: () => _scan(client),
                  icon: const Icon(Icons.qr_code_scanner),
                  label: const Text('Escanear QR'),
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(56),
                  ),
                ),
                const SizedBox(height: 32),
                Text(
                  'O ingresa el enlace a mano',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _url,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  textInputAction: TextInputAction.go,
                  onSubmitted: (text) => _handle(client, text),
                  decoration: const InputDecoration(
                    labelText: 'Enlace a analizar',
                    hintText: 'https://ejemplo.com',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: () => _handle(client, _url.text),
                  icon: const Icon(Icons.search),
                  label: const Text('Analizar'),
                ),
              ],
            ),
    );
  }
}
