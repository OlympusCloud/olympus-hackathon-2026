import 'dart:io' show Platform, exit, stdout;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:olympus_sdk/olympus_sdk.dart';

import 'demo_credentials.dart';

/// Entry point. Behaviour depends on how the binary is invoked:
///
/// - `flutter run -d chrome` → renders the UI in [MyApp].
/// - `dart run --define=HEADLESS=1` (or env `HEADLESS=1`) → runs a single
///   Ceres call and prints the result to stdout. This is the `make demo`
///   path; lets reviewers exercise the end-to-end flow without a browser.
Future<void> main() async {
  if (_isHeadless) {
    await _runHeadlessDemo();
    return;
  }
  runApp(const MyApp());
}

bool get _isHeadless {
  if (kIsWeb) return false;
  return Platform.environment['HEADLESS'] == '1';
}

Future<void> _runHeadlessDemo() async {
  final report = await _callCeres('Generate a low-stock report.');
  stdout.writeln(report);
  exit(0);
}

Future<String> _callCeres(String query) async {
  final client = OlympusClient(
    baseUrl: DemoCredentials.gatewayUrl,
    token: DemoCredentials.tenantJwt,
  );
  final response = await client.agent.chat(
    message: query,
    tenantId: DemoCredentials.tenantId,
    userId: DemoCredentials.userId,
    sessionId: 'hackathon-demo-${DateTime.now().millisecondsSinceEpoch}',
    shellType: 'customer',
    domain: 'inventory',
  );
  return response.message;
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Olympus Hackathon Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const DemoHome(),
    );
  }
}

class DemoHome extends StatefulWidget {
  const DemoHome({super.key});

  @override
  State<DemoHome> createState() => _DemoHomeState();
}

class _DemoHomeState extends State<DemoHome> {
  final TextEditingController _queryCtrl = TextEditingController(
    text: 'Generate a low-stock report.',
  );
  String _output = '';
  bool _loading = false;

  Future<void> _send() async {
    setState(() {
      _loading = true;
      _output = '';
    });
    try {
      final report = await _callCeres(_queryCtrl.text);
      setState(() => _output = report);
    } catch (e, st) {
      setState(() => _output = 'error: $e\n$st');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ceres on Vertex — hackathon demo')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _queryCtrl,
              decoration: const InputDecoration(
                labelText: 'Inventory query',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _loading ? null : _send,
              icon: const Icon(Icons.send),
              label: Text(_loading ? 'Calling…' : 'Ask Ceres'),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: SingleChildScrollView(
                child: SelectableText(
                  _output.isEmpty
                      ? '(report appears here)'
                      : _output,
                  style: const TextStyle(fontFamily: 'monospace'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
