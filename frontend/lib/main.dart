import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/language_selection_screen.dart';

void main() {
  runApp(const swayamfillApp());
}

class swayamfillApp extends StatefulWidget {
  const swayamfillApp({super.key});

  @override
  State<swayamfillApp> createState() => _swayamfillAppState();
  
  static _swayamfillAppState? of(BuildContext context) => 
      context.findAncestorStateOfType<_swayamfillAppState>();
}

class _swayamfillAppState extends State<swayamfillApp> {
  ThemeMode _themeMode = ThemeMode.dark;

  void toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'swayamfill',
      debugShowCheckedModeBanner: false,
      themeMode: _themeMode,
      theme: _buildTheme(Brightness.light),
      darkTheme: _buildTheme(Brightness.dark),
      home: const LanguageSelectionScreen(),
    );
  }

  ThemeData _buildTheme(Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    
    // Premium Dark Palette
    final bg = isDark ? const Color(0xFF0F1115) : const Color(0xFFF8F9FE);
    final surface = isDark ? const Color(0xFF181A20) : Colors.white;
    final primary = const Color(0xFF6C63FF); // Deep Indigo
    final onSurface = isDark ? const Color(0xFFEDEDED) : const Color(0xFF1E1E2C);
    
    var baseTheme = ThemeData(
      brightness: brightness, 
      useMaterial3: true,
      scaffoldBackgroundColor: bg,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        brightness: brightness,
        primary: primary,
        secondary: const Color(0xFF00BFA6), // Teal/Aqua accent
        surface: surface,
        onSurface: onSurface,
        primaryContainer: isDark ? const Color(0xFF242636) : const Color(0xFFEBE9FF),
        onPrimaryContainer: isDark ? const Color(0xFFE0E0FF) : const Color(0xFF241E6F),
      ),
    );

    return baseTheme.copyWith(
      textTheme: GoogleFonts.outfitTextTheme(baseTheme.textTheme).apply(
        bodyColor: onSurface,
        displayColor: onSurface,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: bg,
        foregroundColor: onSurface,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.outfit(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: onSurface,
        ),
      ),
      /*
      cardTheme: CardTheme(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(
            color: isDark ? Colors.white.withOpacity(0.05) : Colors.grey.shade100,
            width: 1,
          ),
        ),
      ),
      */
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: isDark ? const Color(0xFF242636) : Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: primary, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
        hintStyle: GoogleFonts.outfit(
          color: isDark ? Colors.white38 : Colors.grey.shade400,
        ),
      ),
    );
  }
}
