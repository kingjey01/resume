import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../features/upload/screens/record_audio_screen.dart';
import '../features/upload/screens/record_audio_screen_web_safe.dart';

/// Page d'enregistrement audio avec sélection de cours (restaurée)
/// Utilise la version web-safe sur Flutter Web
class RecordingPage extends ConsumerStatefulWidget {
  const RecordingPage({super.key});

  @override
  ConsumerState<RecordingPage> createState() => _RecordingPageState();
}

class _RecordingPageState extends ConsumerState<RecordingPage> {
  @override
  Widget build(BuildContext context) {
    // Sur Web, utiliser la version web-safe
    if (kIsWeb) {
      return const RecordAudioScreenWebSafe();
    }
    
    // Sur mobile, utiliser la version complète (a déjà son propre Scaffold)
    return const RecordAudioScreen();
  }
}