import 'package:flutter/foundation.dart';

/// Logger sécurisé pour production et développement
class AppLogger {
  static void debug(String message, [String? tag]) {
    if (kDebugMode) {
      final timestamp = DateTime.now().toIso8601String();
      final prefix = tag != null ? '[$tag] ' : '';
      print('$timestamp $prefix$message');
    }
  }

  static void error(String message, [Object? error, StackTrace? stackTrace]) {
    if (kDebugMode) {
      final timestamp = DateTime.now().toIso8601String();
      print('$timestamp ERROR: $message');
      if (error != null) {
        print('Error details: $error');
      }
      if (stackTrace != null) {
        print('Stack trace: $stackTrace');
      }
    }
  }

  static void warning(String message, [String? tag]) {
    if (kDebugMode) {
      final timestamp = DateTime.now().toIso8601String();
      final prefix = tag != null ? '[$tag] ' : '';
      print('$timestamp WARNING: $prefix$message');
    }
  }

  static void info(String message, [String? tag]) {
    if (kDebugMode) {
      final timestamp = DateTime.now().toIso8601String();
      final prefix = tag != null ? '[$tag] ' : '';
      print('$timestamp INFO: $prefix$message');
    }
  }
}
