import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qrshield/motor_client.dart';
import 'package:qrshield/result_view.dart';

AnalyzeResult result({
  Verdict verdict = Verdict.red,
  List<String> reasons = const ['acortador de URL', 'TLD sospechoso'],
  List<String> chain = const [
    'https://bit.ly/x',
    'https://t.co/y',
    'https://banco-falso.xyz/login',
  ],
  bool resolved = true,
  String layer = 'L1',
}) => AnalyzeResult(
  verdict: verdict,
  score: 60,
  reasons: reasons,
  finalUrl: chain.last,
  chain: chain,
  chainResolved: resolved,
  totalMs: 412.7,
  decidingLayer: layer,
);

Future<void> show(WidgetTester tester, AnalyzeResult r) => tester.pumpWidget(
  MaterialApp(
    home: Scaffold(body: ResultView(result: r)),
  ),
);

void main() {
  testWidgets('rojo muestra veredicto, motivos y la ruta salto por salto', (
    tester,
  ) async {
    await show(tester, result());

    expect(find.text('Peligroso'), findsOneWidget);
    expect(find.text('Riesgo: 60/100'), findsOneWidget);
    expect(find.text('acortador de URL'), findsOneWidget);
    expect(find.text('TLD sospechoso'), findsOneWidget);
    expect(find.text('https://bit.ly/x'), findsOneWidget);
    expect(find.text('Enlace del QR'), findsOneWidget);
    expect(find.text('Redirección intermedia'), findsOneWidget);
    expect(find.text('Destino final'), findsOneWidget);
    expect(find.textContaining('413 ms'), findsOneWidget);
    expect(find.textContaining('heurísticas locales'), findsOneWidget);
    expect(find.textContaining('No se pudo seguir'), findsNothing);
  });

  testWidgets('verde sin motivos y sin redirecciones', (tester) async {
    await show(
      tester,
      result(
        verdict: Verdict.green,
        reasons: [],
        chain: ['https://www.x.com'],
        layer: 'cascade',
      ),
    );

    expect(find.text('Seguro'), findsOneWidget);
    expect(find.text('No se encontraron señales de riesgo.'), findsOneWidget);
    expect(find.text('El enlace no redirige a otro sitio.'), findsOneWidget);
    expect(find.text('Destino final'), findsNothing);
  });

  testWidgets('cadena sin resolver se advierte', (tester) async {
    await show(tester, result(verdict: Verdict.yellow, resolved: false));

    expect(find.text('Sospechoso'), findsOneWidget);
    expect(find.textContaining('No se pudo seguir'), findsOneWidget);
  });

  testWidgets('el lector de pantalla oye el veredicto, no solo el color', (
    tester,
  ) async {
    final handle = tester.ensureSemantics();
    await show(tester, result());
    expect(
      find.bySemanticsLabel('Veredicto: Peligroso, riesgo 60 de 100'),
      findsOneWidget,
    );
    handle.dispose();
  });
}
