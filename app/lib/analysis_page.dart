import 'package:flutter/material.dart';

import 'motor_client.dart';
import 'result_view.dart';

const _errorMessages = {
  MotorError.unreachable:
      'No se pudo contactar al servicio de análisis. Revisa tu conexión.',
  MotorError.timeout: 'El análisis tardó demasiado. Intenta de nuevo.',
  MotorError.serverError:
      'El servicio de análisis falló. Intenta de nuevo en unos minutos.',
  MotorError.invalidUrl: 'El enlace no es válido y no se pudo analizar.',
  MotorError.badResponse: 'El servicio respondió algo inesperado.',
};

class AnalysisPage extends StatefulWidget {
  final MotorClient client;
  final String url;
  const AnalysisPage({super.key, required this.client, required this.url});

  @override
  State<AnalysisPage> createState() => _AnalysisPageState();
}

class _AnalysisPageState extends State<AnalysisPage> {
  late Future<AnalyzeResult> _result = widget.client.analyze(widget.url);

  // Con cuerpo de bloque: si el callback de setState devuelve el Future, Flutter
  // lo rechaza y el reintento no se aplica.
  void _retry() => setState(() {
    _result = widget.client.analyze(widget.url);
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Resultado')),
      body: FutureBuilder<AnalyzeResult>(
        future: _result,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final result = snap.data;
          if (result == null) {
            // Cualquier fallo cae aca, sin veredicto: nunca se muestra verde.
            final error = snap.error;
            final message = error is MotorException
                ? _errorMessages[error.error]!
                : 'Ocurrió un error inesperado.';
            return _ErrorView(message: message, onRetry: _retry);
          }
          return ResultView(result: result);
        },
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 48),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
