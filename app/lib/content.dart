/// Clasifica el texto de un QR (o el que escribe el usuario). Solo un enlace
/// http(s) va al motor; el resto se informa como "no es un enlace".
library;

sealed class QrContent {
  const QrContent();
}

class LinkContent extends QrContent {
  final String url;
  const LinkContent(this.url);
}

class NotLinkContent extends QrContent {
  /// Descripcion para el usuario: "una red WiFi", "un contacto", ...
  final String kind;
  const NotLinkContent(this.kind);
}

// Host con TLD y sin esquema: `www.x.com`, `x.com:8080/ruta`. Va antes que
// Uri.parse porque este toma `x.com:8080` como esquema `x.com`.
final _bareHost = RegExp(
  r'^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}(:\d+)?([/?#]\S*)?$',
  caseSensitive: false,
);

QrContent classify(String raw) {
  final text = raw.trim();
  if (_bareHost.hasMatch(text)) return LinkContent('https://$text');

  final uri = Uri.tryParse(text);
  if (uri != null &&
      (uri.scheme == 'http' || uri.scheme == 'https') &&
      uri.host.isNotEmpty &&
      !text.contains(RegExp(r'\s'))) {
    return LinkContent(text);
  }

  final upper = text.toUpperCase();
  if (upper.startsWith('WIFI:')) return const NotLinkContent('una red WiFi');
  if (upper.startsWith('BEGIN:VCARD') || upper.startsWith('MECARD:')) {
    return const NotLinkContent('un contacto');
  }
  if (upper.startsWith('MAILTO:')) return const NotLinkContent('un correo');
  if (upper.startsWith('TEL:') || upper.startsWith('SMSTO:')) {
    return const NotLinkContent('un número de teléfono');
  }
  return const NotLinkContent('texto');
}
