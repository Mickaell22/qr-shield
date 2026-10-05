import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

/// Abre la camara y devuelve el texto del primer QR leido, o null si el
/// usuario vuelve sin escanear. En Android la deteccion la hace ML Kit.
Future<String?> scanQr(BuildContext context) => Navigator.of(
  context,
).push<String>(MaterialPageRoute(builder: (_) => const ScannerPage()));

class ScannerPage extends StatefulWidget {
  const ScannerPage({super.key});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> {
  final _controller = MobileScannerController(
    formats: const [BarcodeFormat.qrCode],
  );
  // La camara sigue entregando lecturas mientras se cierra la pantalla:
  // sin esta bandera se apilarian varios pop.
  bool _done = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_done) return;
    for (final code in capture.barcodes) {
      final value = code.rawValue;
      if (value != null && value.isNotEmpty) {
        _done = true;
        Navigator.of(context).pop(value);
        return;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Escanear QR')),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
            errorBuilder: (context, error) => _CameraError(
              denied:
                  error.errorCode == MobileScannerErrorCode.permissionDenied,
              onRetry: _controller.start,
            ),
          ),
          const Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                'Apunta la cámara al código QR',
                style: TextStyle(
                  color: Colors.white,
                  shadows: [Shadow(blurRadius: 4)],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CameraError extends StatelessWidget {
  final bool denied;
  final VoidCallback onRetry;
  const _CameraError({required this.denied, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: Theme.of(context).colorScheme.surface,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.no_photography_outlined, size: 48),
              const SizedBox(height: 16),
              Text(
                denied
                    ? 'Sin permiso de cámara no se puede escanear. Puedes '
                          'concederlo en los ajustes del teléfono o ingresar '
                          'el enlace a mano.'
                    : 'No se pudo abrir la cámara.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: onRetry,
                child: const Text('Reintentar'),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Ingresar el enlace a mano'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
