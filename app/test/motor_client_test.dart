import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:qrshield/motor_client.dart';

Map<String, dynamic> body({String verdict = 'yellow'}) => {
  'verdict': verdict,
  'score': 25,
  'reasons': ['acortador de URL'],
  'final_url': 'https://destino.example/',
  'redirects': {
    'chain': ['https://bit.ly/x', 'https://destino.example/'],
    'hops': 1,
    'resolved': true,
    'rewrote_url': true,
    'reason': '',
  },
  'metrics': {'total_ms': 120.5, 'deciding_layer': 'L1', 'layers': <Object>[]},
};

MotorClient client(MockClientHandler handler) =>
    MotorClient(MockClient(handler), 'http://motor.test/');

Future<MotorError> errorOf(MotorClient c) async {
  try {
    await c.analyze('https://bit.ly/x');
  } on MotorException catch (e) {
    return e.error;
  }
  fail('se esperaba MotorException');
}

void main() {
  test('envia la URL a /v1/analyze y parsea la respuesta', () async {
    late http.Request sent;
    final c = client((req) async {
      sent = req;
      return http.Response(jsonEncode(body()), 200);
    });

    final r = await c.analyze('https://bit.ly/x');

    expect(sent.method, 'POST');
    expect(sent.url.toString(), 'http://motor.test/v1/analyze');
    expect(jsonDecode(sent.body), {'url': 'https://bit.ly/x'});
    expect(r.verdict, Verdict.yellow);
    expect(r.score, 25);
    expect(r.chain, hasLength(2));
    expect(r.decidingLayer, 'L1');
  });

  test('422 es URL invalida', () async {
    expect(
      await errorOf(client((_) async => http.Response('{}', 422))),
      MotorError.invalidUrl,
    );
  });

  test('5xx es error del motor', () async {
    expect(
      await errorOf(client((_) async => http.Response('', 503))),
      MotorError.serverError,
    );
  });

  test('sin conexion es inalcanzable', () async {
    expect(
      await errorOf(client((_) async => throw http.ClientException('sin red'))),
      MotorError.unreachable,
    );
  });

  test('respuesta lenta vence el timeout', () async {
    final c = MotorClient(
      MockClient((_) async {
        await Future<void>.delayed(const Duration(milliseconds: 200));
        return http.Response(jsonEncode(body()), 200);
      }),
      'http://motor.test',
      timeout: const Duration(milliseconds: 50),
    );
    expect(await errorOf(c), MotorError.timeout);
  });

  test('veredicto desconocido o cuerpo roto nunca se vuelve verde', () async {
    expect(
      await errorOf(
        client(
          (_) async => http.Response(jsonEncode(body(verdict: 'ok')), 200),
        ),
      ),
      MotorError.badResponse,
    );
    expect(
      await errorOf(client((_) async => http.Response('no json', 200))),
      MotorError.badResponse,
    );
  });
}
