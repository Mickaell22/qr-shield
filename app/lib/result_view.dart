import 'package:flutter/material.dart';

import 'motor_client.dart';

// El veredicto se comunica con icono y texto ademas del color: el color solo
// no alcanza para daltonismo. Primer plano oscuro sobre fondo claro (>7:1).
const _style = {
  Verdict.green: (
    label: 'Seguro',
    icon: Icons.check_circle,
    fg: Color(0xFF1B5E20),
    bg: Color(0xFFE8F5E9),
  ),
  Verdict.yellow: (
    label: 'Sospechoso',
    icon: Icons.warning_amber_rounded,
    fg: Color(0xFF6D4C00),
    bg: Color(0xFFFFF8E1),
  ),
  Verdict.red: (
    label: 'Peligroso',
    icon: Icons.dangerous,
    fg: Color(0xFFB71C1C),
    bg: Color(0xFFFFEBEE),
  ),
};

// Valores de `deciding_layer` del motor (ver telemetry.deciding_layer).
const _layers = {
  'L1': 'heurísticas locales',
  'L2': 'caché de análisis previos',
  'L3': 'lista de URLs maliciosas (URLhaus)',
  'cascade': 'ninguna capa encontró riesgo',
};

class ResultView extends StatelessWidget {
  final AnalyzeResult result;
  const ResultView({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final s = _style[result.verdict]!;
    final chain = result.chain;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Semantics(
          container: true,
          label: 'Veredicto: ${s.label}, riesgo ${result.score} de 100',
          excludeSemantics: true,
          child: Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: s.bg,
              border: Border.all(color: s.fg, width: 2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(s.icon, color: s.fg, size: 48),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        s.label,
                        style: text.headlineMedium?.copyWith(
                          color: s.fg,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        'Riesgo: ${result.score}/100',
                        style: text.titleMedium?.copyWith(color: s.fg),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text('Motivos', style: text.titleMedium),
        if (result.reasons.isEmpty)
          const ListTile(
            leading: Icon(Icons.verified_outlined),
            title: Text('No se encontraron señales de riesgo.'),
          )
        else
          for (final reason in result.reasons)
            ListTile(
              leading: const Icon(Icons.report_outlined),
              title: Text(reason),
            ),
        const SizedBox(height: 16),
        Text('Ruta del enlace', style: text.titleMedium),
        if (!result.chainResolved)
          const ListTile(
            leading: Icon(Icons.error_outline),
            title: Text(
              'No se pudo seguir la ruta completa: el análisis se hizo '
              'sobre el último salto alcanzado.',
            ),
          ),
        if (chain.length == 1)
          const ListTile(
            leading: Icon(Icons.arrow_forward),
            title: Text('El enlace no redirige a otro sitio.'),
          ),
        for (var i = 0; i < chain.length; i++)
          ListTile(
            leading: CircleAvatar(child: Text('${i + 1}')),
            title: SelectableText(chain[i]),
            subtitle: Text(_hopLabel(i, chain.length)),
          ),
        const SizedBox(height: 16),
        Text(
          'Analizado en ${result.totalMs.round()} ms · Decidió: '
          '${_layers[result.decidingLayer] ?? result.decidingLayer}',
          style: text.bodySmall,
        ),
      ],
    );
  }
}

String _hopLabel(int i, int length) {
  if (i == 0) return 'Enlace del QR';
  if (i == length - 1) return 'Destino final';
  return 'Redirección intermedia';
}
