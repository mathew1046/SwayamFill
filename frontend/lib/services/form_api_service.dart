import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/form_models.dart';

class FormApiService {
  const FormApiService();

  Future<void> saveFieldValues({
    required String backendUrl,
    required String sessionId,
    required Map<String, String> fieldValues,
  }) async {
    final response = await http.put(
      Uri.parse('$backendUrl/session/$sessionId/field-values'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'field_values': fieldValues}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to save field values (${response.statusCode})');
    }
  }

  Future<GenerateFormImageResponseModel> generateFilledForm({
    required String backendUrl,
    required String sessionId,
    required Map<String, String> fieldValues,
  }) async {
    final response = await http.post(
      Uri.parse('$backendUrl/generate-form-image'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'session_id': sessionId,
        'field_values': fieldValues,
        'output_format': 'png',
        'quality': 'medium',
        'background': 'opaque',
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to generate form (${response.statusCode}): ${response.body}');
    }

    return GenerateFormImageResponseModel.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
