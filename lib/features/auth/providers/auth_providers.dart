import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/auth/repositories/auth_repository.dart';

// Provider pour AuthRepository
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});
