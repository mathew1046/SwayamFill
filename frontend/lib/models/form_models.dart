class FormFieldModel {
  final String fieldId;
  final String label;
  final List<int> bbox;
  final String inputMode;
  final String writeLanguage;
  final String? hint;

  const FormFieldModel({
    required this.fieldId,
    required this.label,
    required this.bbox,
    required this.inputMode,
    required this.writeLanguage,
    this.hint,
  });

  factory FormFieldModel.fromJson(Map<String, dynamic> json) {
    return FormFieldModel(
      fieldId: json['field_id'] as String,
      label: json['label'] as String,
      bbox: List<int>.from(json['bbox'] as List),
      inputMode: (json['input_mode'] as String?) ?? 'voice',
      writeLanguage: (json['write_language'] as String?) ?? 'en',
      hint: json['hint'] as String?,
    );
  }
}

class AnalyzeFormResponse {
  final String sessionId;
  final int imageWidth;
  final int imageHeight;
  final List<FormFieldModel> fields;

  const AnalyzeFormResponse({
    required this.sessionId,
    required this.imageWidth,
    required this.imageHeight,
    required this.fields,
  });

  factory AnalyzeFormResponse.fromJson(Map<String, dynamic> json) {
    final fieldsJson = (json['fields'] as List? ?? const []);
    return AnalyzeFormResponse(
      sessionId: json['session_id'] as String,
      imageWidth: (json['image_width'] as num).toInt(),
      imageHeight: (json['image_height'] as num).toInt(),
      fields: fieldsJson
          .whereType<Map>()
          .map((item) => FormFieldModel.fromJson(Map<String, dynamic>.from(item)))
          .toList(),
    );
  }
}

class GenerateFormImageResponseModel {
  final String sessionId;
  final String mimeType;
  final String imageBase64;
  final String generatedImageUrl;

  const GenerateFormImageResponseModel({
    required this.sessionId,
    required this.mimeType,
    required this.imageBase64,
    required this.generatedImageUrl,
  });

  factory GenerateFormImageResponseModel.fromJson(Map<String, dynamic> json) {
    return GenerateFormImageResponseModel(
      sessionId: json['session_id'] as String,
      mimeType: json['mime_type'] as String,
      imageBase64: json['image_base64'] as String,
      generatedImageUrl: json['generated_image_url'] as String,
    );
  }
}
