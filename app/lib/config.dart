/// Configuracion de compilacion. Llega por `--dart-define` o
/// `--dart-define-from-file=.env` (ver `.env.example`), nunca escrita en el codigo.
library;

/// URL base del motor, sin `/v1`. Vacia si no se paso al compilar.
const motorUrl = String.fromEnvironment('MOTOR_URL');

/// Mismo criterio que `PRODUCT_NAME` del motor: el nombre comercial aun no esta
/// cerrado. ponytail: el label de Android (`AndroidManifest.xml`) lo repite; si
/// el nombre cambia son esas dos lineas.
const productName = String.fromEnvironment(
  'PRODUCT_NAME',
  defaultValue: 'Umbral',
);
