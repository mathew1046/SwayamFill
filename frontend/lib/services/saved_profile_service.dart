import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class SavedProfileService {
  static const _storageKey = 'saved_field_profile_v1';

  Future<Map<String, String>> getAllValues() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw == null || raw.isEmpty) {
      return {};
    }

    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, dynamic>) {
      return {};
    }

    return decoded.map((key, value) => MapEntry(key, value.toString()));
  }

  Future<String?> getValueForLabel(String label) async {
    final values = await getAllValues();
    return values[_normalizeLabel(label)];
  }

  Future<void> saveValue(String label, String value) async {
    final cleaned = value.trim();
    if (cleaned.isEmpty) return;

    final prefs = await SharedPreferences.getInstance();
    final values = await getAllValues();
    values[_normalizeLabel(label)] = cleaned;
    await prefs.setString(_storageKey, jsonEncode(values));
  }

  String _normalizeLabel(String label) {
    return label.trim().toLowerCase().replaceAll(RegExp(r'[^a-z0-9]+'), '_');
  }
}
