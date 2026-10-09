import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qrshield/motor_client.dart';
import 'package:qrshield/result_view.dart';

AnalyzeResult result(Verdict verdict, {bool resolved = true}) => AnalyzeResult(
  verdict: verdict,
  score: 0,
  reasons: const [],
  finalUrl: 'https://destino.example/',
  chain: const ['https://bit.ly/x', 'https://destino.example/'],
  chainResolved: resolved,
  totalMs: 10,
  decidingLayer: 'L1',
);

/// Muestra el resultado y devuelve las URLs que se intentaron abrir.
Future<List<Uri>> show(
  WidgetTester tester,
  AnalyzeResult r, {
  bool launchOk = true,
}) async {
  final opened = <Uri>[];
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: ResultView(
          result: r,
          launch: (uri) async {
            opened.add(uri);
            return launchOk;
          },
        ),
      ),
    ),
  );
  return opened;
}

Future<void> tapOpen(WidgetTester tester) async {
  final button = find.textContaining('Abrir');
  // Los SelectableText de la ruta traen su propio Scrollable: se desplaza la lista.
  await tester.scrollUntilVisible(
    button.first,
    200,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.tap(button.first);
  await tester.pumpAndSettle();
}

Future<void> press(WidgetTester tester, String label) async {
  await tester.tap(find.text(label));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('verde abre directo el destino analizado, no la URL del QR', (
    tester,
  ) async {
    final opened = await show(tester, result(Verdict.green));
    await tapOpen(tester);

    expect(find.byType(AlertDialog), findsNothing);
    expect(opened, [Uri.parse('https://destino.example/')]);
  });

  testWidgets('amarillo pide una confirmacion', (tester) async {
    final opened = await show(tester, result(Verdict.yellow));

    await tapOpen(tester);
    await press(tester, 'Cancelar');
    expect(opened, isEmpty);

    await tapOpen(tester);
    await press(tester, 'Continuar');
    expect(opened, hasLength(1));
  });

  testWidgets('rojo pide dos confirmaciones', (tester) async {
    final opened = await show(tester, result(Verdict.red));

    await tapOpen(tester);
    await press(tester, 'Continuar');
    expect(find.text('Última confirmación'), findsOneWidget);
    await press(tester, 'Cancelar');
    expect(opened, isEmpty);

    await tapOpen(tester);
    await press(tester, 'Continuar');
    await press(tester, 'Sí, abrir el enlace');
    expect(opened, hasLength(1));
  });

  testWidgets('verde con la ruta sin resolver no abre directo', (tester) async {
    final opened = await show(tester, result(Verdict.green, resolved: false));

    await tapOpen(tester);
    expect(find.byType(AlertDialog), findsOneWidget);
    expect(opened, isEmpty);
  });

  testWidgets('si el navegador no abre se avisa', (tester) async {
    await show(tester, result(Verdict.green), launchOk: false);
    await tapOpen(tester);

    expect(find.text('No se pudo abrir el enlace.'), findsOneWidget);
  });
}
