import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/services/api_service.dart';

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

final purchasedSummariesProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final apiService = ref.read(apiServiceProvider);
  return await apiService.getPurchasedSummaries();
});
