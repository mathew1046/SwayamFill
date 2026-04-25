import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../models/form_models.dart';
import '../services/form_api_service.dart';
import '../services/saved_profile_service.dart';
import '../services/stt_service.dart';
import '../services/tts_service.dart';
import 'generated_form_screen.dart';

class FieldCollectionScreen extends StatefulWidget {
  final String sessionId;
  final String backendUrl;
  final String selectedLanguage;
  final int imageWidth;
  final int imageHeight;
  final List<FormFieldModel> fields;

  const FieldCollectionScreen({
    super.key,
    required this.sessionId,
    required this.backendUrl,
    required this.selectedLanguage,
    required this.imageWidth,
    required this.imageHeight,
    required this.fields,
  });

  @override
  State<FieldCollectionScreen> createState() => _FieldCollectionScreenState();
}

class _FieldCollectionScreenState extends State<FieldCollectionScreen> {
  final _textController = TextEditingController();
  final _stt = SttService();
  final _tts = TtsService();
  final _profileService = SavedProfileService();
  final _apiService = const FormApiService();

  final Map<String, String> _fieldValues = {};
  final Map<String, SavedFieldMatch> _matchedValues = {};
  final Set<String> _editingMatchedFields = {};

  int _currentIndex = 0;
  bool _isRecording = false;
  bool _isBusy = true;
  Uint8List? _formImage;

  FormFieldModel get _currentField => widget.fields[_currentIndex];
  bool get _isLastField => _currentIndex == widget.fields.length - 1;
  bool get _hasPendingMatchedValue =>
      _matchedValues.containsKey(_currentField.fieldId) &&
      !_editingMatchedFields.contains(_currentField.fieldId);

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  @override
  void dispose() {
    _textController.dispose();
    _stt.dispose();
    _tts.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    await _tts.initialize();
    await _stt.initialize();

    // Load form image in background while the user flow starts.
    final imageLoadFuture = _loadImageInBackground();

    await _preloadSavedValues();
    _syncControllerWithCurrentField();
    await _speakCurrentPrompt();
    if (mounted) {
      setState(() => _isBusy = false);
    }

    // Keep the future alive (errors are already handled internally).
    await imageLoadFuture;
  }

  Future<void> _loadImageInBackground() async {
    try {
      final response = await http.get(
        Uri.parse('${widget.backendUrl}/session/${widget.sessionId}/image'),
      );
      if (response.statusCode == 200 && mounted) {
        setState(() {
          _formImage = response.bodyBytes;
        });
      }
    } catch (_) {
      // Image preview is optional during collection flow.
    }
  }

  Future<void> _preloadSavedValues() async {
    for (final field in widget.fields) {
      final match = await _profileService.getMatchForLabel(field.label);
      if (match != null && match.value.trim().isNotEmpty) {
        _fieldValues[field.fieldId] = match.value.trim();
        _matchedValues[field.fieldId] = match;
      }
    }
  }

  void _syncControllerWithCurrentField() {
    _textController.text = _fieldValues[_currentField.fieldId] ?? '';
  }

  Future<void> _speakCurrentPrompt() async {
    final hintText = _currentField.hint == null ? '' : ' Hint: ${_currentField.hint}.';
    final match = _matchedValues[_currentField.fieldId];
    final prompt = _hasPendingMatchedValue && match != null
        ? 'I found a saved value for ${_currentField.label}: ${match.value}. '
            'If this looks correct, tap Looks Correct. Otherwise tap Correct It.'
        : 'Please enter ${_currentField.label}.$hintText You can type or use the microphone.';
    await _tts.speak(
      prompt,
      backendUrl: widget.backendUrl,
      sessionId: widget.sessionId,
      language: widget.selectedLanguage,
    );
  }

  Future<void> _toggleRecording() async {
    if (_isBusy) return;

    if (!_isRecording) {
      final started = await _stt.startRecording(
        backendUrl: widget.backendUrl,
        language: widget.selectedLanguage,
        sessionId: widget.sessionId,
      );
      if (started) {
        setState(() => _isRecording = true);
      }
      return;
    }

    setState(() {
      _isBusy = true;
      _isRecording = false;
    });

    try {
      final transcript = await _stt.stopAndTranscribe();
      if (transcript != null && transcript.trim().isNotEmpty) {
        _textController.text = transcript.trim();
      }
    } finally {
      if (mounted) {
        setState(() => _isBusy = false);
      }
    }
  }

  Future<void> _goToNextField() async {
    final value = _textController.text.trim();
    if (value.isNotEmpty) {
      _fieldValues[_currentField.fieldId] = value;
      await _profileService.saveValue(_currentField.label, value);
    } else {
      _fieldValues.remove(_currentField.fieldId);
    }

    if (_isLastField) {
      await _generateForm();
      return;
    }

    setState(() {
      _currentIndex += 1;
      _syncControllerWithCurrentField();
    });
    await _speakCurrentPrompt();
  }

  Future<void> _confirmMatchedValue() async {
    if (_isBusy || !_hasPendingMatchedValue) return;
    await _goToNextField();
  }

  Future<void> _editMatchedValue() async {
    if (_isBusy || !_hasPendingMatchedValue) return;

    setState(() {
      _editingMatchedFields.add(_currentField.fieldId);
    });

    await _tts.speak(
      'Please correct ${_currentField.label}. You can type the new value or use the microphone.',
      backendUrl: widget.backendUrl,
      sessionId: widget.sessionId,
      language: widget.selectedLanguage,
    );
  }

  void _goToPreviousField() {
    if (_currentIndex == 0) return;
    setState(() {
      _currentIndex -= 1;
      _syncControllerWithCurrentField();
    });
  }

  Future<void> _generateForm() async {
    setState(() => _isBusy = true);

    try {
      await _apiService.saveFieldValues(
        backendUrl: widget.backendUrl,
        sessionId: widget.sessionId,
        fieldValues: _fieldValues,
      );

      final result = await _apiService.generateFilledForm(
        backendUrl: widget.backendUrl,
        sessionId: widget.sessionId,
        fieldValues: _fieldValues,
      );

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (context) => GeneratedFormScreen(
            sessionId: result.sessionId,
            mimeType: result.mimeType,
            imageBase64: result.imageBase64,
          ),
        ),
      );
    } catch (e) {
      _showError('Generation failed: $e');
      setState(() => _isBusy = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  String _buildHelperText() {
    final match = _matchedValues[_currentField.fieldId];
    if (_hasPendingMatchedValue && match != null) {
      final source = match.sourceLabel.trim().isEmpty ? '' : ' from "${match.sourceLabel}"';
      return 'Matched a previously saved value$source using ${match.matchedBy} label matching.';
    }

    if (_editingMatchedFields.contains(_currentField.fieldId)) {
      return 'Update the saved value if this field has changed for the new form.';
    }

    return 'Saved values from previous forms are reused automatically when the label matches.';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('Field ${_currentIndex + 1} of ${widget.fields.length}'),
      ),
      body: _isBusy && _formImage == null
          ? const Center(child: CircularProgressIndicator())
          : Stack(
              children: [
                Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            _buildImagePreview(),
                            const SizedBox(height: 20),
                            Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.surface,
                                borderRadius: BorderRadius.circular(24),
                                border: Border.all(color: theme.colorScheme.primary.withOpacity(0.12)),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _currentField.label,
                                    style: theme.textTheme.headlineSmall?.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  if ((_currentField.hint ?? '').isNotEmpty) ...[
                                    const SizedBox(height: 8),
                                    Text(
                                      _currentField.hint!,
                                      style: theme.textTheme.bodyMedium?.copyWith(
                                        color: theme.colorScheme.primary,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 16),
                                  TextField(
                                    controller: _textController,
                                    readOnly: _hasPendingMatchedValue,
                                    minLines: 1,
                                    maxLines: 3,
                                    decoration: InputDecoration(
                                      hintText: _hasPendingMatchedValue
                                          ? 'Previously saved value matched for this field'
                                          : 'Type the value here',
                                      suffixIcon: IconButton(
                                        onPressed: _hasPendingMatchedValue ? null : _toggleRecording,
                                        icon: Icon(_isRecording ? Icons.stop_circle : Icons.mic),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  Text(
                                    _buildHelperText(),
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      color: theme.colorScheme.onSurface.withOpacity(0.65),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
                      child: _hasPendingMatchedValue
                          ? Row(
                              children: [
                                Expanded(
                                  child: OutlinedButton.icon(
                                    onPressed: _isBusy ? null : _editMatchedValue,
                                    icon: const Icon(Icons.edit_outlined),
                                    label: const Text('Correct it'),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: FilledButton.icon(
                                    onPressed: _isBusy ? null : _confirmMatchedValue,
                                    icon: const Icon(Icons.check_circle),
                                    label: Text(_isLastField ? 'Use saved value' : 'Looks correct'),
                                  ),
                                ),
                              ],
                            )
                          : Row(
                              children: [
                                Expanded(
                                  child: OutlinedButton(
                                    onPressed: _currentIndex == 0 || _isBusy ? null : _goToPreviousField,
                                    child: const Text('Previous'),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: FilledButton(
                                    onPressed: _isBusy ? null : _goToNextField,
                                    child: Text(_isLastField ? 'Generate Form' : 'Next Field'),
                                  ),
                                ),
                              ],
                            ),
                    ),
                  ],
                ),
                if (_isBusy)
                  Container(
                    color: Colors.black26,
                    child: const Center(child: CircularProgressIndicator()),
                  ),
              ],
            ),
    );
  }

  Widget _buildImagePreview() {
    if (_formImage == null) {
      return const SizedBox.shrink();
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final aspectRatio = widget.imageWidth / widget.imageHeight;
        var previewWidth = constraints.maxWidth;
        var previewHeight = previewWidth / aspectRatio;

        if (previewHeight > 320) {
          previewHeight = 320;
          previewWidth = previewHeight * aspectRatio;
        }

        return Center(
          child: SizedBox(
            width: previewWidth,
            height: previewHeight,
            child: Stack(
              children: [
                Positioned.fill(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(18),
                    child: Image.memory(_formImage!, fit: BoxFit.contain),
                  ),
                ),
                Positioned.fill(
                  child: CustomPaint(
                    painter: _FieldHighlightPainter(
                      bbox: _currentField.bbox,
                      imageWidth: widget.imageWidth,
                      imageHeight: widget.imageHeight,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _FieldHighlightPainter extends CustomPainter {
  final List<int> bbox;
  final int imageWidth;
  final int imageHeight;

  _FieldHighlightPainter({
    required this.bbox,
    required this.imageWidth,
    required this.imageHeight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final scaleX = size.width / imageWidth;
    final scaleY = size.height / imageHeight;

    final rect = Rect.fromLTRB(
      bbox[0] * scaleX,
      bbox[1] * scaleY,
      bbox[2] * scaleX,
      bbox[3] * scaleY,
    );

    final fillPaint = Paint()
      ..color = const Color(0xFF22C55E).withOpacity(0.18)
      ..style = PaintingStyle.fill;
    final borderPaint = Paint()
      ..color = const Color(0xFF16A34A)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    canvas.drawRect(rect, fillPaint);
    canvas.drawRect(rect, borderPaint);
  }

  @override
  bool shouldRepaint(covariant _FieldHighlightPainter oldDelegate) {
    return oldDelegate.bbox != bbox;
  }
}
