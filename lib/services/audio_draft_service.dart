import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Données d'un brouillon audio.
class AudioDraft {
  final String id;
  String? audioFilePath; // chemin local du fichier (mobile)
  Uint8List? audioBytes; // bytes (web ou fallback)
  String? mimeType;
  String? fileName;
  int? courseId;
  String? courseName;
  String? title;
  double? price;
  int duration; // secondes
  DateTime createdAt;
  String? professeurNom;
  int? professeurId;

  AudioDraft({
    required this.id,
    this.audioFilePath,
    this.audioBytes,
    this.mimeType,
    this.fileName,
    this.courseId,
    this.courseName,
    this.title,
    this.price,
    this.duration = 0,
    DateTime? createdAt,
    this.professeurNom,
    this.professeurId,
  }) : createdAt = createdAt ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'id': id,
        'audioFilePath': audioFilePath,
        'mimeType': mimeType,
        'fileName': fileName,
        'courseId': courseId,
        'courseName': courseName,
        'title': title,
        'price': price,
        'duration': duration,
        'createdAt': createdAt.toIso8601String(),
        'professeurNom': professeurNom,
        'professeurId': professeurId,
      };

  factory AudioDraft.fromJson(Map<String, dynamic> json) => AudioDraft(
        id: json['id'] as String? ?? '',
        audioFilePath: json['audioFilePath'] as String?,
        mimeType: json['mimeType'] as String?,
        fileName: json['fileName'] as String?,
        courseId: json['courseId'] as int?,
        courseName: json['courseName'] as String?,
        title: json['title'] as String?,
        price: (json['price'] as num?)?.toDouble(),
        duration: json['duration'] as int? ?? 0,
        createdAt: json['createdAt'] != null
            ? DateTime.tryParse(json['createdAt'] as String) ?? DateTime.now()
            : DateTime.now(),
        professeurNom: json['professeurNom'] as String?,
        professeurId: json['professeurId'] as int?,
      );

  String get durationFormatted {
    final h = duration ~/ 3600;
    final m = (duration % 3600) ~/ 60;
    if (h > 0) return '${h}h ${m}min';
    return '${m} min';
  }
}

/// Service de gestion des brouillons audio multiples.
///
/// Chaque brouillon est indépendant, avec son propre ID.
/// Limitée à [maxDrafts] brouillons simultanés.
///
/// Stockage :
/// - fichier audio → `getApplicationDocumentsDirectory()/drafts/{id}/`
/// - métadonnées (liste JSON) → SharedPreferences
class AudioDraftService {
  static const String _draftListKey = 'audio_draft_list';
  static const String _draftDir = 'drafts';
  static const int maxDrafts = 5;

  // ─── Singleton ──────────────────────────────────────────────────
  static final AudioDraftService _instance = AudioDraftService._internal();
  factory AudioDraftService() => _instance;
  AudioDraftService._internal();

  // ─── CRUD : Liste ───────────────────────────────────────────────

  /// Récupère tous les brouillons (métadonnées uniquement).
  Future<List<AudioDraft>> listDrafts() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_draftListKey);
    if (raw == null) return [];

    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list
          .map((e) => AudioDraft.fromJson(e as Map<String, dynamic>))
          .where((d) => d.id.isNotEmpty)
          .toList()
        ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
    } catch (e) {
      print('⚠️ AudioDraft: erreur lecture liste: $e');
      return [];
    }
  }

  // ─── CRUD : Ajouter ─────────────────────────────────────────────

  /// Ajoute un brouillon. Retourne `true` si succès, `false` si limite atteinte.
  Future<bool> addDraft(AudioDraft draft) async {
    final drafts = await listDrafts();

    if (drafts.length >= maxDrafts) {
      print('⚠️ AudioDraft: limite de $maxDrafts brouillons atteinte');
      return false;
    }

    // Sauvegarder le fichier audio
    if (draft.audioBytes != null && draft.audioFilePath == null) {
      final filePath = await _writeAudioFile(
        draft.audioBytes!,
        '${draft.id}.${_extensionFromMime(draft.mimeType ?? 'audio/m4a')}',
      );
      draft.audioFilePath = filePath;
    }

    drafts.insert(0, draft);
    await _persistList(drafts);
    print('💾 AudioDraft: brouillon ajouté (${draft.fileName}) — total: ${drafts.length}');
    return true;
  }

  // ─── CRUD : Récupérer un brouillon ──────────────────────────────

  /// Récupère un brouillon par son ID.
  Future<AudioDraft?> getDraft(String id) async {
    final drafts = await listDrafts();
    try {
      return drafts.firstWhere((d) => d.id == id);
    } catch (_) {
      return null;
    }
  }

  /// Récupère les bytes audio d'un brouillon.
  Future<Uint8List?> loadDraftAudio(String id) async {
    final draft = await getDraft(id);
    if (draft == null) return null;

    if (draft.audioBytes != null) return draft.audioBytes;
    if (draft.audioFilePath != null) {
      try {
        final file = File(draft.audioFilePath!);
        if (await file.exists()) return await file.readAsBytes();
      } catch (e) {
        print('⚠️ AudioDraft: erreur lecture fichier $id: $e');
      }
    }
    return null;
  }

  // ─── CRUD : Mettre à jour les métadonnées ───────────────────────

  /// Met à jour les métadonnées d'un brouillon existant.
  Future<void> updateDraft(AudioDraft updated) async {
    final drafts = await listDrafts();
    final index = drafts.indexWhere((d) => d.id == updated.id);
    if (index == -1) return;

    drafts[index] = updated;
    await _persistList(drafts);
    print('💾 AudioDraft: brouillon mis à jour (${updated.id})');
  }

  // ─── CRUD : Supprimer ───────────────────────────────────────────

  /// Supprime un brouillon par son ID (fichier + métadonnées).
  Future<void> deleteDraft(String id) async {
    // Supprimer le fichier audio
    final draft = await getDraft(id);
    if (draft?.audioFilePath != null) {
      try {
        final file = File(draft!.audioFilePath!);
        if (await file.exists()) await file.delete();
      } catch (e) {
        print('⚠️ AudioDraft: erreur suppression fichier $id: $e');
      }
    }

    // Supprimer de la liste
    final drafts = await listDrafts();
    drafts.removeWhere((d) => d.id == id);
    await _persistList(drafts);
    print('🗑️ AudioDraft: brouillon supprimé ($id) — restants: ${drafts.length}');
  }

  // ─── CRUD : Compter ─────────────────────────────────────────────

  /// Nombre de brouillons actuels.
  Future<int> count() async {
    final drafts = await listDrafts();
    return drafts.length;
  }

  /// Vérifie si la limite est atteinte.
  Future<bool> isFull() async {
    return await count() >= maxDrafts;
  }

  /// Places disponibles.
  Future<int> remaining() async {
    return maxDrafts - await count();
  }

  // ─── Persistance ────────────────────────────────────────────────

  Future<void> _persistList(List<AudioDraft> drafts) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(drafts.map((d) => d.toJson()).toList());
    await prefs.setString(_draftListKey, encoded);
  }

  // ─── Helper fichier ─────────────────────────────────────────────

  Future<String> _writeAudioFile(Uint8List bytes, String fileName) async {
    final dir = await getApplicationDocumentsDirectory();
    final draftDir = Directory('${dir.path}/$_draftDir');
    if (!await draftDir.exists()) {
      await draftDir.create(recursive: true);
    }

    final file = File('${draftDir.path}/$fileName');
    await file.writeAsBytes(bytes);
    return file.path;
  }

  String _extensionFromMime(String mime) {
    switch (mime) {
      case 'audio/wav':
        return 'wav';
      case 'audio/mp3':
      case 'audio/mpeg':
        return 'mp3';
      case 'audio/ogg':
      case 'audio/webm':
        return 'ogg';
      default:
        return 'm4a';
    }
  }
}
