import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'motor_client.dart';

typedef Launcher = Future<bool> Function(Uri uri);

Future<bool> launchExternal(Uri uri) =>
    launchUrl(uri, mode: LaunchMode.externalApplication);

/// Cuantas confirmaciones pide abrir el enlace: verde 0, amarillo 1, rojo 2.
/// Una cadena sin resolver nunca abre directo: el analisis corrio sobre un
/// salto intermedio, asi que un verde ahi no garantiza el destino real.
/// El rojo no se bloquea del todo: castigaria los falsos positivos.
int confirmationsFor(AnalyzeResult r) => switch (r.verdict) {
  Verdict.red => 2,
  Verdict.yellow => 1,
  Verdict.green => r.chainResolved ? 0 : 1,
};

/// Abre la URL analizada (`final_url`), no la del QR: si se abriera la del QR
/// el navegador recorreria de nuevo las redirecciones y un QR dinamico podria
/// llevar a otro destino distinto del que se analizo.
Future<void> openAnalyzedLink(
  BuildContext context,
  AnalyzeResult result,
  Launcher launch,
) async {
  final steps = confirmationsFor(result);
  if (steps >= 1 &&
      !await _confirm(
        context,
        title: '¿Abrir este enlace?',
        body: result.verdict == Verdict.red
            ? 'El análisis lo clasificó como peligroso. Puede robar tus '
                  'datos o instalar software malicioso.'
            : 'El análisis encontró señales de riesgo. Ábrelo solo si '
                  'confías en quien te dio el código.',
        accept: 'Continuar',
      )) {
    return;
  }
  if (steps >= 2 &&
      context.mounted &&
      !await _confirm(
        context,
        title: 'Última confirmación',
        body:
            'No ingreses contraseñas, datos bancarios ni códigos de '
            'verificación en este sitio.\n\n${result.finalUrl}',
        accept: 'Sí, abrir el enlace',
      )) {
    return;
  }

  var opened = false;
  try {
    opened = await launch(Uri.parse(result.finalUrl));
  } catch (_) {
    opened = false;
  }
  if (!opened && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('No se pudo abrir el enlace.')),
    );
  }
}

Future<bool> _confirm(
  BuildContext context, {
  required String title,
  required String body,
  required String accept,
}) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: Text(body),
      actions: [
        // La opcion segura es la destacada.
        FilledButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancelar'),
        ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: Text(accept),
        ),
      ],
    ),
  );
  return ok ?? false;
}
