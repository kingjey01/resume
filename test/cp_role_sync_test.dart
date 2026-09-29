// Non-régression : détection et propagation du statut CP après
// authentification / restauration de session.
//
// Bug corrigé : `currentUserRoleProvider` renvoyait « ETUDIANT » quand le rôle
// n'était PAS ENCORE CONNU (profil global en cours de chargement / en erreur).
// L'écran d'accueil écrasait alors son rôle déjà connu (CP) par cette valeur,
// ce qui réaffichait la bannière « devenir CP » et masquait le bouton « + »
// d'un CP déjà validé, jusqu'à un rafraîchissement manuel.

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:resume_plus_clean/features/app/screens/main_navigation_screen.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart';
import 'package:resume_plus_clean/features/auth/repositories/auth_repository.dart';
import 'package:resume_plus_clean/features/home/screens/home_screen.dart';
import 'package:resume_plus_clean/models/user.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/notification_service.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

// ─────────────────────────── Profils de test ───────────────────────────

Map<String, dynamic> _profile(String groupe) => {
      'id': 1,
      'username': 'utilisateur',
      'email': 'u@test.com',
      'first_name': 'Jean',
      'last_name': 'Test',
      'profile': {
        'groupe': groupe,
        'universite': 1, // non null : sinon l'écran redirige vers la
        'promotion': 1, //   complétion de profil
        'filiere': 1,
        'phone': '0102030405',
        'cp_onboarding_completed': true,
      },
    };

final _cpUser = User(
  id: 1,
  username: 'utilisateur',
  email: 'u@test.com',
  groupe: 'CP',
  cpOnboardingCompleted: true,
);

final _etudiant = User(
  id: 1,
  username: 'utilisateur',
  email: 'u@test.com',
  groupe: 'ETUDIANT',
);

// ─────────────────────── Authentification de test ──────────────────────

class _MockStorageService extends Mock implements StorageService {}

/// Notifier dont on pilote l'état directement (aucun réseau).
class _TestAuthNotifier extends AuthNotifier {
  _TestAuthNotifier(StorageService storage)
      : super(AuthRepository(storageService: storage), storage, ApiService());

  void emit(AsyncValue<User?> value) => state = value;
}

/// Storage dont [readTokens] ne se termine jamais → le notifier reste en
/// `AsyncValue.loading` (profil global « pas encore chargé », cas du bug).
StorageService _loadingStorage() {
  final storage = _MockStorageService();
  when(() => storage.readTokens())
      .thenAnswer((_) => Completer<Map<String, String?>>().future);
  return storage;
}

// ──────────────────────── Fausse couche HTTP ───────────────────────────

class _MockHttpClient extends Mock implements HttpClient {}

class _MockHttpClientRequest extends Mock implements HttpClientRequest {}

class _MockHttpHeaders extends Mock implements HttpHeaders {}

/// En-têtes de réponse factices exposant un content-type JSON à dio.
_MockHttpHeaders _jsonHeaders() {
  final headers = _MockHttpHeaders();
  when(() => headers[any()])
      .thenReturn(const ['application/json; charset=utf-8']);
  when(() => headers.forEach(any())).thenAnswer((invocation) {
    final action = invocation.positionalArguments[0]
        as void Function(String name, List<String> values);
    action('content-type', const ['application/json; charset=utf-8']);
  });
  return headers;
}

class _FakeHttpClientResponse extends StreamView<List<int>>
    implements HttpClientResponse {
  _FakeHttpClientResponse(String body, {required this.statusCode})
      : _bytes = utf8.encode(body),
        super(Stream<List<int>>.fromIterable([utf8.encode(body)]));

  final List<int> _bytes;

  @override
  final int statusCode;

  @override
  String get reasonPhrase => 'OK';

  @override
  int get contentLength => _bytes.length;

  @override
  HttpHeaders get headers => _jsonHeaders();

  @override
  bool get isRedirect => false;

  @override
  bool get persistentConnection => false;

  @override
  List<RedirectInfo> get redirects => const <RedirectInfo>[];

  @override
  HttpClientResponseCompressionState get compressionState =>
      HttpClientResponseCompressionState.notCompressed;

  @override
  X509Certificate? get certificate => null;

  @override
  HttpConnectionInfo? get connectionInfo => null;

  @override
  List<Cookie> get cookies => const <Cookie>[];

  @override
  Future<HttpClientResponse> redirect(
          [String? method, Uri? url, bool? followLoops]) =>
      throw UnimplementedError();

  @override
  Future<Socket> detachSocket() => throw UnimplementedError();
}

class _FakeHttpOverrides extends HttpOverrides {
  _FakeHttpOverrides(this.client);

  final HttpClient client;

  @override
  HttpClient createHttpClient(SecurityContext? context) => client;
}

/// Installe une couche HTTP factice : chaque clé de [routes] est comparée à la
/// fin du chemin de la requête ; tout le reste répond 404.
void _installFakeHttp(Map<String, String> routes) {
  final client = _MockHttpClient();
  when(() => client.openUrl(any(), any())).thenAnswer((invocation) async {
    final uri = invocation.positionalArguments[1] as Uri;
    String? body;
    for (final entry in routes.entries) {
      if (uri.path.endsWith(entry.key)) {
        body = entry.value;
        break;
      }
    }
    final request = _MockHttpClientRequest();
    when(() => request.headers).thenReturn(_MockHttpHeaders());
    when(() => request.close()).thenAnswer(
      (_) async => _FakeHttpClientResponse(
        body ?? '{}',
        statusCode: body == null ? 404 : 200,
      ),
    );
    return request;
  });

  HttpOverrides.global = _FakeHttpOverrides(client);
  addTearDown(() {
    HttpOverrides.global = null;
    NotificationService().stopPolling();
  });
}

/// Routes minimales pour que l'écran d'accueil se charge sans erreur.
///
/// [cpStatus] permet de simuler une demande déjà en attente ou une promotion
/// déjà couverte (tache34, point 3).
Map<String, String> _routes({
  required String groupe,
  Map<String, dynamic>? cpStatus,
}) =>
    {
      '/auth/user/': jsonEncode(_profile(groupe)),
      '/summaries/': '[]',
      '/course-list/': '[]',
      '/auth/cp-request/status/': jsonEncode(
        cpStatus ?? {'request': null, 'combination_blocked': false},
      ),
    };

/// Monte [HomeScreen] puis exécute [corps] avant d'arrêter le polling de
/// notifications : le `Timer.periodic` démarré par l'écran doit être annulé
/// AVANT la fin du test, sinon flutter_test échoue (« A Timer is still
/// pending »).
Future<void> _avecHome(
  WidgetTester tester,
  AuthNotifier notifier,
  Future<void> Function() corps,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [authProvider.overrideWith((ref) => notifier)],
      child: MaterialApp(
        theme: AppTheme.lightTheme,
        home: const HomeScreen(),
      ),
    ),
  );
  try {
    // Laisse partir la requête de profil locale puis revenir la réponse.
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 20));
    }
    await corps();
  } finally {
    // Laisse se terminer les requêtes encore en vol : sinon le timer de
    // timeout de dio reste actif et flutter_test échoue
    // (« A Timer is still pending »).
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 20));
    }
    NotificationService().stopPolling();
  }
}

Finder _fabPlus() => find.byIcon(Icons.add);
Finder _banniereCP() => find.text('Devenez Chef de Promotion');

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() {
    registerFallbackValue(Uri.parse('https://exemple.test/'));
  });

  setUp(() {
    // Le stockage des jetons passe par un canal natif : sans handler, l'appel
    // ne se termine jamais sous FakeAsync et l'intercepteur d'API (qui attend
    // le token) bloque toutes les requêtes.
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
      const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
      (call) async => null,
    );
  });

  // ───────── Le rôle « inconnu » n'est PAS « ETUDIANT » ─────────
  group('currentUserRoleProvider', () {
    ProviderContainer containerAvec(_TestAuthNotifier notifier) {
      final container = ProviderContainer(
        overrides: [authProvider.overrideWith((ref) => notifier)],
      );
      addTearDown(container.dispose);
      return container;
    }

    test('renvoie null tant que le rôle n\'est pas connu', () {
      final notifier = _TestAuthNotifier(_loadingStorage());
      final container = containerAvec(notifier);

      expect(container.read(currentUserRoleProvider), isNull); // loading
      notifier.emit(const AsyncValue.loading());
      expect(container.read(currentUserRoleProvider), isNull);
      notifier.emit(AsyncValue.error('réseau', StackTrace.empty));
      expect(container.read(currentUserRoleProvider), isNull);
      notifier.emit(const AsyncValue.data(null)); // déconnecté
      expect(container.read(currentUserRoleProvider), isNull);
    });

    test('expose le rôle réel dès que le profil est chargé', () {
      final notifier = _TestAuthNotifier(_loadingStorage());
      final container = containerAvec(notifier);

      notifier.emit(AsyncValue.data(_cpUser));
      expect(container.read(currentUserRoleProvider), 'CP');

      notifier.emit(AsyncValue.data(_etudiant));
      expect(container.read(currentUserRoleProvider), 'ETUDIANT');
    });

    test("les fournisseurs dérivés ne lancent pas d'exception en chargement ou en erreur", () {
      final notifier = _TestAuthNotifier(_loadingStorage());
      final container = containerAvec(notifier);

      // Erreur réseau : « inconnu » et non une exception relancée.
      notifier.emit(AsyncValue.error('réseau', StackTrace.empty));
      expect(container.read(currentUserRoleProvider), isNull);
      expect(container.read(currentUserProvider), isNull);
      expect(container.read(isAuthenticatedProvider), isFalse);

      notifier.emit(const AsyncValue.loading());
      expect(container.read(currentUserProvider), isNull);
      expect(container.read(isAuthenticatedProvider), isFalse);

      // Le chemin nominal reste inchangé.
      notifier.emit(AsyncValue.data(_cpUser));
      expect(container.read(currentUserProvider)?.id, _cpUser.id);
      expect(container.read(isAuthenticatedProvider), isTrue);
    });

    test('prévient ses consommateurs quand le rôle devient connu', () async {
      final notifier = _TestAuthNotifier(_loadingStorage());
      final container = containerAvec(notifier);
      final vus = <String?>[];
      container.listen(
        currentUserRoleProvider,
        (_, next) => vus.add(next),
        fireImmediately: true,
      );

      notifier.emit(AsyncValue.data(_cpUser));
      await Future<void>.delayed(Duration.zero); // livraison des listeners
      expect(vus, [null, 'CP']);
    });
  });

  // ───────── Écran d'accueil : bannière CP et bouton « + » ─────────
  group('HomeScreen', () {
    testWidgets(
        'CP déjà validé, profil global encore en chargement : bouton « + » '
        'visible et aucune bannière de demande CP', (tester) async {
      _installFakeHttp(_routes(groupe: 'CP'));
      final notifier = _TestAuthNotifier(_loadingStorage()); // rôle global inconnu
      await _avecHome(tester, notifier, () async {
        expect(_fabPlus(), findsOneWidget);
        expect(_banniereCP(), findsNothing);
        expect(tester.takeException(), isNull);
      });
    });

    testWidgets(
        'CP déjà validé : le rôle reste connu même si l\'état global repasse '
        'en chargement (restauration / rafraîchissement)', (tester) async {
      _installFakeHttp(_routes(groupe: 'CP'));
      final notifier = _TestAuthNotifier(_loadingStorage());
      await _avecHome(tester, notifier, () async {
        notifier.emit(AsyncValue.data(_cpUser));
        await tester.pump();
        expect(_fabPlus(), findsOneWidget);

        // Rechargement global (retour d'arrière-plan, relance, refresh) :
        // l'état repasse par « loading ». Le rôle connu ne doit pas être perdu.
        notifier.emit(const AsyncValue.loading());
        await tester.pump();
        expect(_fabPlus(), findsOneWidget);
        expect(_banniereCP(), findsNothing);
      });
    });

    testWidgets('CP connu de l\'état global : bouton « + » visible sans profil local',
        (tester) async {
      _installFakeHttp(const {}); // le profil local échoue (404)
      final notifier = _TestAuthNotifier(_loadingStorage())
        ..emit(AsyncValue.data(_cpUser));
      await _avecHome(tester, notifier, () async {
        expect(_fabPlus(), findsOneWidget);
        expect(_banniereCP(), findsNothing);
      });
    });

    testWidgets('utilisateur non CP : comportement conservé (bannière, pas de bouton « + »)',
        (tester) async {
      _installFakeHttp(_routes(groupe: 'ETUDIANT'));
      final notifier = _TestAuthNotifier(_loadingStorage());
      await _avecHome(tester, notifier, () async {
        expect(_banniereCP(), findsOneWidget);
        expect(_fabPlus(), findsNothing);
      });
    });

    testWidgets('rafraîchissement manuel : toujours correct', (tester) async {
      _installFakeHttp(_routes(groupe: 'CP'));
      final notifier = _TestAuthNotifier(_loadingStorage())
        ..emit(AsyncValue.data(_cpUser));
      await _avecHome(tester, notifier, () async {
        await tester.tap(find.byIcon(Icons.refresh_rounded));
        for (var i = 0; i < 5; i++) {
          await tester.pump(const Duration(milliseconds: 20));
        }
        expect(_fabPlus(), findsOneWidget);
        expect(_banniereCP(), findsNothing);
        expect(tester.takeException(), isNull);
      });
    });

    testWidgets(
        'état global en ERREUR : pas de plantage, rôle local conservé '
        '(bouton « + » visible, aucune bannière)', (tester) async {
      _installFakeHttp(_routes(groupe: 'CP'));
      final notifier = _TestAuthNotifier(_loadingStorage())
        ..emit(AsyncValue.error('réseau', StackTrace.empty));

      await _avecHome(tester, notifier, () async {
        expect(tester.takeException(), isNull);
        expect(_fabPlus(), findsOneWidget);
        expect(_banniereCP(), findsNothing);
      });
    });
  });

  // ───────── Demande CP impossible : card totalement masqué (tache34) ─────────
  group('HomeScreen — demande CP impossible', () {
    testWidgets(
        'demande en attente : le card de demande CP n\'est plus affiché du tout',
        (tester) async {
      _installFakeHttp(_routes(
        groupe: 'ETUDIANT',
        cpStatus: {
          'has_request': true,
          'request': {'status': 'pending'},
          'combination_blocked': true,
        },
      ));
      final notifier = _TestAuthNotifier(_loadingStorage());

      await _avecHome(tester, notifier, () async {
        // Ni le card, ni son ancienne version « grisée ».
        expect(_banniereCP(), findsNothing);
        expect(find.text('Demande en cours de traitement'), findsNothing);
        expect(find.text('Demander'), findsNothing);
        expect(tester.takeException(), isNull);
      });
    });

    testWidgets(
        'promotion déjà couverte : le card de demande CP n\'est plus affiché du tout',
        (tester) async {
      _installFakeHttp(_routes(
        groupe: 'ETUDIANT',
        cpStatus: {'request': null, 'combination_blocked': true},
      ));
      final notifier = _TestAuthNotifier(_loadingStorage());

      await _avecHome(tester, notifier, () async {
        expect(_banniereCP(), findsNothing);
        expect(find.text('Promotion déjà couverte'), findsNothing);
        expect(find.text('Demander'), findsNothing);
        expect(tester.takeException(), isNull);
      });
    });

    testWidgets(
        'demande refusée : la possibilité de redemander est conservée '
        '(le card reste affiché)', (tester) async {
      _installFakeHttp(_routes(
        groupe: 'ETUDIANT',
        cpStatus: {
          'has_request': true,
          'request': {'status': 'rejected'},
          'combination_blocked': false,
        },
      ));
      final notifier = _TestAuthNotifier(_loadingStorage());

      await _avecHome(tester, notifier, () async {
        expect(_banniereCP(), findsOneWidget);
        expect(find.text('Demander'), findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    });
  });

  // ───────── Barre de navigation (onglets CP) ─────────
  group('MainNavigationScreen', () {
    testWidgets('état global en ERREUR : la barre se construit sans planter',
        (tester) async {
      _installFakeHttp(_routes(groupe: 'CP'));
      final notifier = _TestAuthNotifier(_loadingStorage())
        ..emit(AsyncValue.error('réseau', StackTrace.empty));

      await tester.pumpWidget(
        ProviderScope(
          overrides: [authProvider.overrideWith((ref) => notifier)],
          child: MaterialApp(
            theme: AppTheme.lightTheme,
            home: const MainNavigationScreen(),
          ),
        ),
      );
      try {
        for (var i = 0; i < 10; i++) {
          await tester.pump(const Duration(milliseconds: 100));
        }
        expect(tester.takeException(), isNull);
        // Rôle CP chargé localement → 5 onglets, dont « Validation ».
        expect(find.text('Validation'), findsOneWidget);
        expect(find.text('Accueil'), findsOneWidget);
      } finally {
        NotificationService().stopPolling();
      }
    });
  });
}
