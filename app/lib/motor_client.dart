import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

enum Verdict { green, yellow, red }

/// Respuesta de `POST /v1/analyze`, solo con lo que muestra la app.
class AnalyzeResult {
  final Verdict verdict;
  final int score;
  final List<String> reasons;
  final String finalUrl;

  /// Cadena de redirecciones completa (RF-009): el primer elemento es la URL
  /// del QR y el ultimo el destino alcanzado.
  final List<String> chain;
  final bool chainResolved;
  final double totalMs;
  final String decidingLayer;

  const AnalyzeResult({
    required this.verdict,
    required this.score,
    required this.reasons,
    required this.finalUrl,
    required this.chain,
    required this.chainResolved,
    required this.totalMs,
    required this.decidingLayer,
  });

  /// Lanza si falta un campo o el veredicto es desconocido: una respuesta rara
  /// nunca puede terminar mostrandose como verde.
  factory AnalyzeResult.fromJson(Map<String, dynamic> json) {
    final redirects = json['redirects'] as Map<String, dynamic>;
    final metrics = json['metrics'] as Map<String, dynamic>;
    return AnalyzeResult(
      verdict: Verdict.values.byName(json['verdict'] as String),
      score: json['score'] as int,
      reasons: List<String>.from(json['reasons'] as List),
      finalUrl: json['final_url'] as String,
      chain: List<String>.from(redirects['chain'] as List),
      chainResolved: redirects['resolved'] as bool,
      totalMs: (metrics['total_ms'] as num).toDouble(),
      decidingLayer: metrics['deciding_layer'] as String,
    );
  }
}

enum MotorError {
  /// Sin red, DNS fallido o motor que no acepta conexiones.
  unreachable,
  timeout,

  /// 5xx: el motor esta arriba pero fallo.
  serverError,

  /// 422: el motor rechazo la URL.
  invalidUrl,

  /// Codigo inesperado o cuerpo que no respeta el contrato.
  badResponse,
}

class MotorException implements Exception {
  final MotorError error;
  const MotorException(this.error);

  @override
  String toString() => 'MotorException($error)';
}

class MotorClient {
  final http.Client _http;
  final Uri _endpoint;
  final Duration timeout;

  MotorClient(
    this._http,
    String baseUrl, {
    this.timeout = const Duration(seconds: 5),
  }) : _endpoint = Uri.parse(
         '${baseUrl.replaceAll(RegExp(r'/+$'), '')}/v1/analyze',
       );

  /// Toda falla sale como [MotorException]; nunca devuelve un resultado por
  /// defecto.
  Future<AnalyzeResult> analyze(String url) async {
    final http.Response response;
    try {
      response = await _http
          .post(
            _endpoint,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'url': url}),
          )
          .timeout(timeout);
    } on TimeoutException {
      throw const MotorException(MotorError.timeout);
    } on http.ClientException {
      throw const MotorException(MotorError.unreachable);
    }

    final status = response.statusCode;
    if (status == 422) throw const MotorException(MotorError.invalidUrl);
    if (status >= 500) throw const MotorException(MotorError.serverError);
    if (status != 200) throw const MotorException(MotorError.badResponse);

    try {
      return AnalyzeResult.fromJson(
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
      );
    } catch (_) {
      throw const MotorException(MotorError.badResponse);
    }
  }
}
