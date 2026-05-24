import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:olympus_hackathon_demo/main.dart';

void main() {
  testWidgets('Demo home renders the query field and Ask button', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MyApp());
    expect(find.text('Ceres on Vertex — hackathon demo'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.text('Ask Ceres'), findsOneWidget);
  });
}
