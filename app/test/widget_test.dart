import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:qrshield/main.dart';
import 'package:qrshield/motor_client.dart';

final _green = {
  'verdict': 'green',
  'score': 0,
  'reasons': <String>[],
  'final_url': 'https://www.x.com',
  'redirects': {
    'chain': ['https://www.x.com'],
    'hops': 0,
    'resolved': true,
    'rewrote_url': false,
  },
  'metrics': {'total_ms': 80.0, 'deciding_layer': 'cascade', 'layers': []},
};

App appWith(MockClientHandler handler) =>
    App(client: MotorClient(MockClient(handler), 'http://motor.test'));

Future<void> analyze(WidgetTester tester, String text) async {
  await tester.enterText(find.byType(TextField), text);
  await tester.tap(find.text('Analizar'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('sin MOTOR_URL avisa y no deja analizar', (tester) async {
    await tester.pumpWidget(const App(client: null));
    expect(find.textContaining('MOTOR_URL'), findsOneWidget);
    expect(find.byType(TextField), findsNothing);
  });

  testWidgets('contenido que no es enlace no llega al motor', (tester) async {
    var calls = 0;
    await tester.pumpWidget(
      appWith((_) async {
        calls++;
        return http.Response('', 500);
      }),
    );

    await analyze(tester, 'WIFI:T:WPA;S:casa;P:clave;;');

    expect(
      find.text('El contenido es una red WiFi, no un enlace.'),
      findsOneWidget,
    );
    expect(calls, 0);
  });

  testWidgets('enlace sin esquema se analiza con https', (tester) async {
    String? sent;
    await tester.pumpWidget(
      appWith((req) async {
        sent = (jsonDecode(req.body) as Map)['url'] as String;
        return http.Response(jsonEncode(_green), 200);
      }),
    );

    await analyze(tester, 'www.x.com');

    expect(sent, 'https://www.x.com');
    expect(find.text('Seguro'), findsOneWidget);
  });

  testWidgets('error del motor no muestra veredicto y permite reintentar', (
    tester,
  ) async {
    var fail = true;
    await tester.pumpWidget(
      appWith(
        (_) async => fail
            ? http.Response('', 503)
            : http.Response(jsonEncode(_green), 200),
      ),
    );

    await analyze(tester, 'https://www.x.com');
    expect(find.textContaining('falló'), findsOneWidget);
    expect(find.text('Seguro'), findsNothing);

    fail = false;
    await tester.tap(find.text('Reintentar'));
    await tester.pumpAndSettle();
    expect(find.text('Seguro'), findsOneWidget);
  });
}
