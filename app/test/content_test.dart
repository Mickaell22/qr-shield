import 'package:flutter_test/flutter_test.dart';
import 'package:qrshield/content.dart';

String? link(String raw) => switch (classify(raw)) {
  LinkContent(:final url) => url,
  NotLinkContent() => null,
};

String? kind(String raw) => switch (classify(raw)) {
  LinkContent() => null,
  NotLinkContent(:final kind) => kind,
};

void main() {
  test('http(s) pasa tal cual', () {
    expect(link('https://bit.ly/abc'), 'https://bit.ly/abc');
    expect(link('  http://x.com/a?b=1  '), 'http://x.com/a?b=1');
  });

  test('enlace sin esquema se completa con https', () {
    expect(link('www.x.com'), 'https://www.x.com');
    expect(link('x.com:8080/ruta'), 'https://x.com:8080/ruta');
  });

  test('otros contenidos no son enlaces', () {
    expect(kind('WIFI:T:WPA;S:casa;P:clave;;'), 'una red WiFi');
    expect(kind('BEGIN:VCARD\nFN:Ana\nEND:VCARD'), 'un contacto');
    expect(kind('mailto:a@b.com'), 'un correo');
    expect(kind('tel:+593999'), 'un número de teléfono');
    expect(kind('hola mundo'), 'texto');
    expect(kind('ftp://x.com/a'), 'texto');
    expect(kind('javascript:alert(1)'), 'texto');
    expect(kind('https://x.com/a b'), 'texto');
    expect(kind(''), 'texto');
  });
}
