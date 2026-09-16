import 'package:flutter_test/flutter_test.dart';
import 'package:weather_gpt/main.dart';

void main() {
  testWidgets('WeatherGPT loads', (tester) async {
    await tester.pumpWidget(const WeatherGptApp());
    expect(find.text('WeatherGPT 🌤️'), findsOneWidget);
    expect(find.textContaining('Hi! I’m WeatherGPT.'), findsOneWidget);
  });
}
