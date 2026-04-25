import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class SavedFieldMatch {
  final String value;
  final String sourceLabel;
  final String matchedBy;

  const SavedFieldMatch({
    required this.value,
    required this.sourceLabel,
    required this.matchedBy,
  });
}

class _SavedFieldEntry {
  final String label;
  final String value;
  final String? canonicalKey;

  const _SavedFieldEntry({
    required this.label,
    required this.value,
    required this.canonicalKey,
  });

  factory _SavedFieldEntry.fromJson(Map<String, dynamic> json) {
    return _SavedFieldEntry(
      label: (json['label'] as String?) ?? '',
      value: (json['value'] as String?) ?? '',
      canonicalKey: json['canonical_key'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'label': label,
      'value': value,
      'canonical_key': canonicalKey,
    };
  }
}

class SavedProfileService {
  static const _storageKey = 'saved_field_profile_v2';
  static const _legacyStorageKey = 'saved_field_profile_v1';

  Future<Map<String, String>> getAllValues() async {
    final entries = await _loadEntries();
    return entries.map((key, value) => MapEntry(key, value.value));
  }

  Future<SavedFieldMatch?> getMatchForLabel(String label) async {
    final requestedLabel = label.trim();
    if (requestedLabel.isEmpty) {
      return null;
    }

    final requestedKey = _normalizeLabel(requestedLabel);
    final entries = await _loadEntries();
    final exact = entries[requestedKey];
    if (exact != null && exact.value.trim().isNotEmpty) {
      return SavedFieldMatch(
        value: exact.value.trim(),
        sourceLabel: exact.label,
        matchedBy: 'exact',
      );
    }

    final requestedCanonical = _canonicalKey(requestedLabel);
    if (requestedCanonical != null) {
      final canonicalMatches = entries.values
          .where((entry) =>
              entry.value.trim().isNotEmpty &&
              entry.canonicalKey == requestedCanonical)
          .toList();
      if (canonicalMatches.length == 1) {
        final match = canonicalMatches.single;
        return SavedFieldMatch(
          value: match.value.trim(),
          sourceLabel: match.label,
          matchedBy: 'canonical',
        );
      }
    }

    final requestedTokens = _tokensForLabel(requestedLabel);
    _SavedFieldEntry? bestEntry;
    double bestScore = 0;
    bool tied = false;

    for (final entry in entries.values) {
      final candidateValue = entry.value.trim();
      if (candidateValue.isEmpty) {
        continue;
      }

      final score = _similarityScore(requestedTokens, _tokensForLabel(entry.label));
      if (score > bestScore) {
        bestScore = score;
        bestEntry = entry;
        tied = false;
      } else if ((score - bestScore).abs() < 0.01) {
        tied = true;
      }
    }

    if (bestEntry == null || tied || bestScore < 0.74) {
      return null;
    }

    return SavedFieldMatch(
      value: bestEntry.value.trim(),
      sourceLabel: bestEntry.label,
      matchedBy: 'fuzzy',
    );
  }

  Future<String?> getValueForLabel(String label) async {
    final match = await getMatchForLabel(label);
    return match?.value;
  }

  Future<void> saveValue(String label, String value) async {
    final cleanedLabel = label.trim();
    final cleanedValue = value.trim();
    if (cleanedLabel.isEmpty || cleanedValue.isEmpty) {
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final entries = await _loadEntries();
    final key = _normalizeLabel(cleanedLabel);
    entries[key] = _SavedFieldEntry(
      label: cleanedLabel,
      value: cleanedValue,
      canonicalKey: _canonicalKey(cleanedLabel),
    );

    final payload = entries.map((key, value) => MapEntry(key, value.toJson()));
    await prefs.setString(_storageKey, jsonEncode(payload));
  }

  Future<Map<String, _SavedFieldEntry>> _loadEntries() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw != null && raw.isNotEmpty) {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        return decoded.map((key, value) {
          if (value is Map<String, dynamic>) {
            return MapEntry(key, _SavedFieldEntry.fromJson(value));
          }
          return MapEntry(
            key,
            _SavedFieldEntry(
              label: key,
              value: value.toString(),
              canonicalKey: _canonicalKey(key),
            ),
          );
        });
      }
    }

    final legacyRaw = prefs.getString(_legacyStorageKey);
    if (legacyRaw == null || legacyRaw.isEmpty) {
      return {};
    }

    final decoded = jsonDecode(legacyRaw);
    if (decoded is! Map<String, dynamic>) {
      return {};
    }

    return decoded.map(
      (key, value) => MapEntry(
        key,
        _SavedFieldEntry(
          label: key.replaceAll('_', ' ').trim(),
          value: value.toString(),
          canonicalKey: _canonicalKey(key),
        ),
      ),
    );
  }

  String _normalizeLabel(String label) {
    return label.trim().toLowerCase().replaceAll(RegExp(r'[^a-z0-9]+'), '_');
  }

  String _normalizeForMatching(String label) {
    return label
        .trim()
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9]+'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }

  Set<String> _tokensForLabel(String label) {
    const stopWords = {
      'the',
      'a',
      'an',
      'of',
      'for',
      'your',
      'applicant',
      'candidate',
      'please',
      'enter',
      'details',
      'detail',
      'info',
      'information',
      'no',
      'number',
    };

    return _normalizeForMatching(label)
        .split(' ')
        .where((token) => token.isNotEmpty && !stopWords.contains(token))
        .toSet();
  }

  double _similarityScore(Set<String> left, Set<String> right) {
    if (left.isEmpty || right.isEmpty) {
      return 0;
    }

    final intersection = left.intersection(right).length.toDouble();
    final union = left.union(right).length.toDouble();
    final overlap = intersection / union;

    if (left.containsAll(right) || right.containsAll(left)) {
      return overlap + 0.2;
    }

    return overlap;
  }

  String? _canonicalKey(String label) {
    final normalized = _normalizeForMatching(label);
    if (normalized.isEmpty) {
      return null;
    }

    final patterns = <MapEntry<RegExp, String>>[
      MapEntry(RegExp(r'\b(date of birth|dob|birth date)\b'), 'date_of_birth'),
      MapEntry(RegExp(r'\b(father(?:s)? name|name of father)\b'), 'father_name'),
      MapEntry(RegExp(r'\b(mother(?:s)? name|name of mother)\b'), 'mother_name'),
      MapEntry(RegExp(r'\b(spouse(?:s)? name|husband(?:s)? name|wife(?:s)? name)\b'), 'spouse_name'),
      MapEntry(RegExp(r'\b(address|permanent address|current address|residential address)\b'), 'address'),
      MapEntry(RegExp(r'\b(mobile|mobile number|phone|phone number|contact number|telephone)\b'), 'phone_number'),
      MapEntry(RegExp(r'\b(email|e mail|email address)\b'), 'email'),
      MapEntry(RegExp(r'\b(aadhaar|aadhar|uid)\b'), 'aadhaar_number'),
      MapEntry(RegExp(r'\b(pan|pan number)\b'), 'pan_number'),
      MapEntry(RegExp(r'\b(pin code|postal code|zip code|pincode)\b'), 'postal_code'),
      MapEntry(RegExp(r'\b(gender|sex)\b'), 'gender'),
      MapEntry(RegExp(r'\b(nationality)\b'), 'nationality'),
      MapEntry(RegExp(r'\b(occupation|profession)\b'), 'occupation'),
      MapEntry(RegExp(r'\b(full name|applicant name|candidate name|employee name|student name)\b'), 'full_name'),
    ];

    for (final entry in patterns) {
      if (entry.key.hasMatch(normalized)) {
        return entry.value;
      }
    }

    if (RegExp(r'^(name|your name)$').hasMatch(normalized)) {
      return 'full_name';
    }

    return null;
  }
}
