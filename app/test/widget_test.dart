import 'package:flutter_test/flutter_test.dart';
import 'package:qrshield/main.dart';

void main() {
  testWidgets('sin MOTOR_URL avisa que falta la configuracion', (tester) async {
    await tester.pumpWidget(const App());
    expect(find.text('Falta configurar MOTOR_URL al compilar.'), findsOneWidget);
  });
}
