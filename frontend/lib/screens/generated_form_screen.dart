import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:universal_html/html.dart' as html;

import 'language_selection_screen.dart';

class GeneratedFormScreen extends StatelessWidget {
  final String sessionId;
  final String mimeType;
  final String imageBase64;

  const GeneratedFormScreen({
    super.key,
    required this.sessionId,
    required this.mimeType,
    required this.imageBase64,
  });

  Uint8List get _imageBytes => base64Decode(imageBase64);

  String get _dataUrl => 'data:$mimeType;base64,$imageBase64';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Filled Form Ready'),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  'Your form has been generated in a handwritten style. Download or print it, then sign the document physically.',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
              ),
              const SizedBox(height: 20),
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(24),
                    color: Colors.white,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.08),
                        blurRadius: 18,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(24),
                    child: InteractiveViewer(
                      child: Image.memory(
                        _imageBytes,
                        fit: BoxFit.contain,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: () => _downloadImage(),
                icon: const Icon(Icons.download_rounded),
                label: const Text('Download Filled Form'),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => _printImage(),
                icon: const Icon(Icons.print_rounded),
                label: const Text('Print'),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () {
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(
                      builder: (context) => const LanguageSelectionScreen(),
                    ),
                    (route) => false,
                  );
                },
                child: const Text('Fill Another Form'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _downloadImage() {
    final fileExtension = mimeType.split('/').last;
    final filename = 'filled-form-$sessionId.$fileExtension';

    if (!kIsWeb) {
      return;
    }

    final anchor = html.AnchorElement(href: _dataUrl)
      ..download = filename
      ..style.display = 'none';
    html.document.body?.append(anchor);
    anchor.click();
    anchor.remove();
  }

  void _printImage() {
    if (!kIsWeb) {
      return;
    }

    html.window.open(_dataUrl, '_blank');
  }
}
