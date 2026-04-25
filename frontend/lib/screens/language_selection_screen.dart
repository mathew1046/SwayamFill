import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'upload_screen.dart';

/// Language model with native and English names
class Language {
  final String code;
  final String nativeName;
  final String englishName;

  const Language({
    required this.code,
    required this.nativeName,
    required this.englishName,
  });
}

/// All 11 languages supported by Sarvam AI
const List<Language> supportedLanguages = [
  Language(code: 'hi-IN', nativeName: 'हिन्दी', englishName: 'Hindi'),
  Language(code: 'bn-IN', nativeName: 'বাংলা', englishName: 'Bengali'),
  Language(code: 'kn-IN', nativeName: 'ಕನ್ನಡ', englishName: 'Kannada'),
  Language(code: 'ml-IN', nativeName: 'മലയാളം', englishName: 'Malayalam'),
  Language(code: 'mr-IN', nativeName: 'मराठी', englishName: 'Marathi'),
  Language(code: 'od-IN', nativeName: 'ଓଡ଼ିଆ', englishName: 'Odia'),
  Language(code: 'pa-IN', nativeName: 'ਪੰਜਾਬੀ', englishName: 'Punjabi'),
  Language(code: 'ta-IN', nativeName: 'தமிழ்', englishName: 'Tamil'),
  Language(code: 'te-IN', nativeName: 'తెలుగు', englishName: 'Telugu'),
  Language(code: 'gu-IN', nativeName: 'ગુજરાતી', englishName: 'Gujarati'),
  Language(code: 'en-IN', nativeName: 'English', englishName: 'English'),
];

// Translations for UI elements for all 11 Sarvam AI languages
final Map<String, Map<String, String>> uiTranslations = {
  'hi-IN': {
    'select_language': 'अपनी भाषा चुनें',
    'choose_language': 'फॉर्म भरने के लिए अपनी भाषा चुनें',
    'upload_form': 'फॉर्म अपलोड करें',
    'take_photo': 'फोटो लें',
    'select_gallery': 'गैलरी से चुनें',
    'use_camera': 'कैमरा का उपयोग करें',
    'select_first': 'कृपया पहले एक भाषा चुनें',
    'continue': 'जारी रखने के लिए भाषा चुनें',
  },
  'bn-IN': {
    'select_language': 'আপনার ভাষা নির্বাচন করুন',
    'choose_language': 'ফর্ম পূরণ করতে আপনার ভাষা চয়ন করুন',
    'upload_form': 'ফর্ম আপলোড করুন',
    'take_photo': 'ছবি তুলুন',
    'select_gallery': 'গ্যালারি থেকে নির্বাচন করুন',
    'use_camera': 'ক্যামেরা ব্যবহার করুন',
    'select_first': 'অনুগ্রহ করে প্রথমে একটি ভাষা নির্বাচন করুন',
    'continue': 'চালিয়ে যেতে একটি ভাষা নির্বাচন করুন',
  },
  'kn-IN': {
    'select_language': 'ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
    'choose_language': 'ಫಾರ್ಮ್ ಭರ್ತಿ ಮಾಡಲು ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆರಿಸಿ',
    'upload_form': 'ಫಾರ್ಮ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
    'take_photo': 'ಫೋಟೋ ತೆಗೆಯಿರಿ',
    'select_gallery': 'ಗ್ಯಾಲರಿಯಿಂದ ಆಯ್ಕೆಮಾಡಿ',
    'use_camera': 'ಕ್ಯಾಮರಾ ಬಳಸಿ',
    'select_first': 'ದಯವಿಟ್ಟು ಮೊದಲು ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
    'continue': 'ಮುಂದುವರಿಸಲು ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
  },
  'ml-IN': {
    'select_language': 'നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക',
    'choose_language': 'ഫോം പൂരിപ്പിക്കാൻ ഉപയോഗിക്കുന്ന ഭാഷ തിരഞ്ഞെടുക്കുക',
    'upload_form': 'ഫോം അപ്‌ലോഡ് ചെയ്യുക',
    'take_photo': 'ഫോട്ടോ എടുക്കുക',
    'select_gallery': 'ഗാലറിയിൽ നിന്ന് തിരഞ്ഞെടുക്കുക',
    'use_camera': 'ക്യാമറ ഉപയോഗിക്കുക',
    'select_first': 'ദയവായി ആദ്യം ഒരു ഭാഷ തിരഞ്ഞെടുക്കുക',
    'continue': 'തുടരാൻ ഒരു ഭാഷ തിരഞ്ഞെടുക്കുക',
  },
  'mr-IN': {
    'select_language': 'तुमची भाषा निवडा',
    'choose_language': 'फॉर्म भरण्यासाठी तुमची भाषा निवडा',
    'upload_form': 'फॉर्म अपलोड करा',
    'take_photo': 'फोटो घ्या',
    'select_gallery': 'गॅलरीमधून निवडा',
    'use_camera': 'कॅमेरा वापरा',
    'select_first': 'कृपया प्रथम भाषा निवडा',
    'continue': 'सुरू ठेवण्यासाठी भाषा निवडा',
  },
  'od-IN': {
    'select_language': 'ଆପଣଙ୍କର ଭାଷା ଚୟନ କରନ୍ତୁ',
    'choose_language': 'ଫର୍ମ ପୂରଣ କରିବାକୁ ଆପଣଙ୍କର ଭାଷା ବାଛନ୍ତୁ',
    'upload_form': 'ଫର୍ମ ଅପଲୋଡ୍ କରନ୍ତୁ',
    'take_photo': 'ଫଟୋ ନିଅନ୍ତୁ',
    'select_gallery': 'ଗ୍ୟାଲେରୀରୁ ଚୟନ କରନ୍ତୁ',
    'use_camera': 'କ୍ୟାମେରା ବ୍ୟବହାର କରନ୍ତୁ',
    'select_first': 'ଦୟାକରି ପ୍ରଥମେ ଏକ ଭାଷା ଚୟନ କରନ୍ତୁ',
    'continue': 'ଜାରି ରଖିବାକୁ ଏକ ଭାଷା ଚୟନ କରନ୍ତୁ',
  },
  'pa-IN': {
    'select_language': 'ਆਪਣੀ ਭਾਸ਼ਾ ਚੁਣੋ',
    'choose_language': 'ਫਾਰਮ ਭਰਨ ਲਈ ਆਪਣੀ ਭਾਸ਼ਾ ਚੁਣੋ',
    'upload_form': 'ਫਾਰਮ ਅੱਪਲੋਡ ਕਰੋ',
    'take_photo': 'ਫੋਟੋ ਲਓ',
    'select_gallery': 'ਗੈਲਰੀ ਤੋਂ ਚੁਣੋ',
    'use_camera': 'ਕੈਮਰਾ ਵਰਤੋ',
    'select_first': 'ਕਿਰਪਾ ਕਰਕੇ ਪਹਿਲਾਂ ਇੱਕ ਭਾਸ਼ਾ ਚੁਣੋ',
    'continue': 'ਜਾਰੀ ਰੱਖਣ ਲਈ ਭਾਸ਼ਾ ਚੁਣੋ',
  },
  'ta-IN': {
    'select_language': 'உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்',
    'choose_language': 'படிவத்தை நிரப்ப உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்',
    'upload_form': 'படிவத்தை பதிவேற்றவும்',
    'take_photo': 'புகைப்படம் எடுக்கவும்',
    'select_gallery': 'கேலரியில் இருந்து தேர்ந்தெடுக்கவும்',
    'use_camera': 'கேமராவைப் பயன்படுத்தவும்',
    'select_first': 'தயவுசெய்து முதலில் ஒரு மொழியைத் தேர்ந்தெடுக்கவும்',
    'continue': 'தொடர ஒரு மொழியைத் தேர்ந்தெடுக்கவும்',
  },
  'te-IN': {
    'select_language': 'మీ భాషను ఎంచుకోండి',
    'choose_language': 'ఫారమ్‌ను పూరించడానికి మీ భాషను ఎంచుకోండి',
    'upload_form': 'ఫారమ్‌ను అప్‌లోడ్ చేయండి',
    'take_photo': 'ఫోటో తీయండి',
    'select_gallery': 'గ్యాలరీ నుండి ఎంచుకోండి',
    'use_camera': 'కెమెరాను ఉపయోగించండి',
    'select_first': 'దయచేసి ముందుగా భాషను ఎంచుకోండి',
    'continue': 'కొనసాగించడానికి భాషను ఎంచుకోండి',
  },
  'gu-IN': {
    'select_language': 'તમારી ભાષા પસંદ કરો',
    'choose_language': 'ફોર્મ ભરવા માટે તમારી ભાષા પસંદ કરો',
    'upload_form': 'ફોર્મ અપલોડ કરો',
    'take_photo': 'ફોટો લો',
    'select_gallery': 'ગેલેરીમાંથી પસંદ કરો',
    'use_camera': 'કેમેરા વાપરો',
    'select_first': 'કૃપા કરીને પહેલા ભાષા પસંદ કરો',
    'continue': 'ચાલુ રાખવા ભાષા પસંદ કરો',
  },
  'en-IN': {
    'select_language': 'Select Your Language',
    'choose_language': 'Choose the language you\'ll use to fill the form',
    'upload_form': 'Upload Form Image',
    'take_photo': 'Take a Photo',
    'select_gallery': 'Select from gallery',
    'use_camera': 'Use camera to scan',
    'select_first': 'Please select a language first',
    'continue': 'Select a language to continue',
  },
};

String getTranslation(String key, String? langCode) {
  if (langCode == null) return uiTranslations['en-IN']![key]!;
  return uiTranslations[langCode]?[key] ?? uiTranslations['en-IN']![key]!;
}

class LanguageSelectionScreen extends StatefulWidget {
  const LanguageSelectionScreen({super.key});

  @override
  State<LanguageSelectionScreen> createState() => _LanguageSelectionScreenState();
}

class _LanguageSelectionScreenState extends State<LanguageSelectionScreen> {
  Language? _selectedLanguage;

  void _proceedToUpload(ImageSource source) {
    if (_selectedLanguage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(getTranslation('select_first', _selectedLanguage?.code)),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => UploadScreenWithLanguage(
          selectedLanguage: _selectedLanguage!.code,
          imageSource: source,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 48),
              
              // Header
              Text(
                getTranslation('select_language', _selectedLanguage?.code),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.displaySmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.onSurface,
                  letterSpacing: -1,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                getTranslation('choose_language', _selectedLanguage?.code),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Colors.grey.shade600,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 48),
              
              // Language Dropdown
              Container(
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: _selectedLanguage != null 
                      ? Theme.of(context).colorScheme.primary
                      : Colors.grey.shade300,
                    width: 2,
                  ),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<Language>(
                    value: _selectedLanguage,
                    hint: Text(
                      'Choose a language',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 16,
                      ),
                    ),
                    isExpanded: true,
                    icon: Icon(
                      Icons.arrow_drop_down_rounded,
                      color: Theme.of(context).colorScheme.primary,
                      size: 32,
                    ),
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Theme.of(context).colorScheme.onSurface,
                    ),
                    dropdownColor: Theme.of(context).colorScheme.surface,
                    borderRadius: BorderRadius.circular(16),
                    items: supportedLanguages.map((Language language) {
                      return DropdownMenuItem<Language>(
                        value: language,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Flexible(
                              child: Text(
                                language.nativeName,
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.w500,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text(
                              language.englishName,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                    onChanged: (Language? newValue) {
                      setState(() {
                        _selectedLanguage = newValue;
                      });
                    },
                  ),
                ),
              ),
              
              const SizedBox(height: 48),
              
              // Action buttons
              if (_selectedLanguage != null) ...[
                _buildActionButton(
                  context,
                  icon: Icons.upload_file,
                  label: getTranslation('upload_form', _selectedLanguage?.code),
                  subtitle: getTranslation('select_gallery', _selectedLanguage?.code),
                  onPressed: () => _proceedToUpload(ImageSource.gallery),
                  isPrimary: true,
                ),
                const SizedBox(height: 16),
                _buildActionButton(
                  context,
                  icon: Icons.camera_alt_outlined,
                  label: getTranslation('take_photo', _selectedLanguage?.code),
                  subtitle: getTranslation('use_camera', _selectedLanguage?.code),
                  onPressed: () => _proceedToUpload(ImageSource.camera),
                  isPrimary: false,
                ),
              ] else ...[
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.amber.shade50,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.amber.shade200),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.info_outline, color: Colors.amber.shade700),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          getTranslation('continue', _selectedLanguage?.code),
                          style: TextStyle(
                            color: Colors.amber.shade900,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required String subtitle,
    required VoidCallback onPressed,
    required bool isPrimary,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16),
        child: Ink(
          decoration: BoxDecoration(
            gradient: isPrimary
                ? LinearGradient(
                    colors: [
                      Theme.of(context).colorScheme.primary,
                      Theme.of(context).colorScheme.primary.withOpacity(0.8),
                    ],
                  )
                : null,
            color: isPrimary ? null : Theme.of(context).colorScheme.surface,
            borderRadius: BorderRadius.circular(16),
            border: isPrimary
                ? null
                : Border.all(
                    color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                    width: 2,
                  ),
            boxShadow: [
              BoxShadow(
                color: isPrimary
                    ? Theme.of(context).colorScheme.primary.withOpacity(0.3)
                    : Colors.black.withOpacity(0.05),
                blurRadius: isPrimary ? 12 : 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: isPrimary
                      ? Colors.white.withOpacity(0.2)
                      : Theme.of(context).colorScheme.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: isPrimary ? Colors.white : Theme.of(context).colorScheme.primary,
                  size: 28,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: isPrimary
                            ? Colors.white
                            : Theme.of(context).colorScheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: isPrimary
                            ? Colors.white.withOpacity(0.8)
                            : Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.arrow_forward_ios_rounded,
                color: isPrimary ? Colors.white : Theme.of(context).colorScheme.primary,
                size: 20,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
