import 'package:resume_plus_clean/models/summary.dart' as model;

/// 🎭 Service de données de démonstration pour le Web
class DemoDataService {
  static final DemoDataService _instance = DemoDataService._internal();
  factory DemoDataService() => _instance;
  DemoDataService._internal();

  /// Données de démonstration pour les résumés
  static List<model.Summary> get demoSummaries => [
    model.Summary(
      id: 1,
      title: 'Résumé IA - Programmation Python',
      subject: 'Informatique',
      imageUrl: 'https://via.placeholder.com/300x200/3776AB/FFFFFF?text=Python',
      content: '''
# Introduction à la Programmation Python

Python est un langage de programmation de haut niveau, interprété et orienté objet. Il est largement utilisé dans le développement web, l'analyse de données, l'intelligence artificielle et l'automatisation.

## Caractéristiques principales

### Syntaxe simple et lisible
Python privilégie la lisibilité du code avec une syntaxe claire et concise. Les blocs de code sont délimités par l'indentation plutôt que par des accolades.

### Typage dynamique
Les variables n'ont pas besoin d'être déclarées avec un type spécifique. Python détermine automatiquement le type lors de l'exécution.

### Bibliothèques étendues
Python dispose d'une vaste collection de bibliothèques standard et tierces pour diverses applications :
- NumPy et Pandas pour l'analyse de données
- Django et Flask pour le développement web
- TensorFlow et PyTorch pour l'apprentissage automatique

## Concepts fondamentaux

### Variables et types de données
Python supporte plusieurs types de données natifs : entiers, flottants, chaînes de caractères, listes, dictionnaires et tuples.

### Structures de contrôle
Les boucles for et while, ainsi que les conditions if-elif-else permettent de contrôler le flux d'exécution du programme.

### Fonctions
Les fonctions permettent d'organiser le code en blocs réutilisables. Python supporte les fonctions lambda pour les opérations simples.

## Programmation orientée objet

Python supporte pleinement la programmation orientée objet avec les classes, l'héritage, l'encapsulation et le polymorphisme.

## Applications pratiques

Python est utilisé dans de nombreux domaines :
- Développement web avec Django et Flask
- Science des données avec Jupyter Notebooks
- Intelligence artificielle et apprentissage automatique
- Automatisation et scripts système
- Développement de jeux avec Pygame

## Conclusion

Python est un excellent choix pour les débutants grâce à sa syntaxe intuitive, tout en restant suffisamment puissant pour les applications professionnelles complexes.
      ''',
      authorName: 'IA Assistant',
      price: 0.0,
      isFree: true,
      createdAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
    model.Summary(
      id: 2,
      title: 'Mathématiques - Analyse Fonctionnelle',
      subject: 'Mathématiques',
      imageUrl: 'https://via.placeholder.com/300x200/FF9800/FFFFFF?text=Math',
      content: '''
# Analyse Fonctionnelle - Concepts Fondamentaux

L'analyse fonctionnelle est une branche des mathématiques qui étudie les espaces vectoriels munis de structures topologiques et les applications linéaires entre ces espaces.

## Espaces vectoriels normés

Un espace vectoriel normé est un espace vectoriel E muni d'une norme, c'est-à-dire d'une application qui associe à chaque vecteur x un nombre réel positif ||x|| satisfaisant certaines propriétés.

### Propriétés de la norme
1. ||x|| ≥ 0 et ||x|| = 0 si et seulement si x = 0
2. ||λx|| = |λ| ||x|| pour tout scalaire λ
3. ||x + y|| ≤ ||x|| + ||y|| (inégalité triangulaire)

## Espaces de Banach

Un espace de Banach est un espace vectoriel normé complet, c'est-à-dire dans lequel toute suite de Cauchy converge.

### Exemples d'espaces de Banach
- L'espace des fonctions continues sur un compact
- Les espaces Lp pour 1 ≤ p ≤ ∞
- L'espace des suites bornées

## Espaces de Hilbert

Un espace de Hilbert est un espace vectoriel muni d'un produit scalaire complet. C'est une généralisation des espaces euclidiens en dimension infinie.

### Théorème de projection
Dans un espace de Hilbert, tout élément peut être projeté orthogonalement sur un sous-espace fermé.

## Applications linéaires continues

Une application linéaire T entre espaces normés est continue si et seulement si elle est bornée, c'est-à-dire s'il existe une constante M telle que ||T(x)|| ≤ M||x||.

## Théorèmes fondamentaux

### Théorème de Hahn-Banach
Ce théorème permet d'étendre une forme linéaire continue définie sur un sous-espace à l'espace tout entier.

### Théorème de Banach-Steinhaus
Aussi appelé principe de la borne uniforme, il établit des conditions pour la convergence uniforme d'une famille d'opérateurs.

## Applications

L'analyse fonctionnelle trouve des applications dans :
- La résolution d'équations aux dérivées partielles
- La théorie quantique en physique
- L'optimisation et le calcul des variations
- Le traitement du signal et l'analyse harmonique

Cette discipline constitue un outil puissant pour l'étude de nombreux problèmes mathématiques et physiques.
      ''',
      authorName: 'Prof. Martin',
      price: 2500.0,
      isFree: false,
      createdAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
    model.Summary(
      id: 3,
      title: 'Histoire - La Renaissance Européenne',
      subject: 'Histoire',
      imageUrl: 'https://via.placeholder.com/300x200/8BC34A/FFFFFF?text=Histoire',
      content: '''
# La Renaissance Européenne (XIVe-XVIe siècles)

La Renaissance marque une période de renouveau culturel, artistique et intellectuel en Europe, caractérisée par un retour aux valeurs antiques et une transformation profonde de la société.

## Contexte historique

### Fin du Moyen Âge
La Renaissance émerge dans un contexte de mutations profondes :
- Déclin de la féodalité
- Essor des villes et de la bourgeoisie marchande
- Développement du commerce international
- Affaiblissement du pouvoir papal

### Foyers de la Renaissance
L'Italie, particulièrement Florence, Venise et Rome, constitue le berceau du mouvement avant de se diffuser vers le nord de l'Europe.

## Humanisme et redécouverte de l'Antiquité

### L'humanisme
Mouvement intellectuel qui place l'homme au centre de ses préoccupations, valorisant :
- L'étude des textes antiques
- L'éducation et la formation de l'esprit
- La dignité de la personne humaine

### Redécouverte des textes anciens
Les humanistes redécouvrent et traduisent les œuvres de Platon, Aristote, Cicéron, contribuant à la diffusion du savoir antique.

## Révolutions artistiques

### Innovations techniques
- Perspective linéaire et aérienne
- Étude anatomique du corps humain
- Utilisation de la peinture à l'huile
- Architecture inspirée de l'antique

### Grands maîtres
- Léonard de Vinci : génie universel, peintre, inventeur, scientifique
- Michel-Ange : sculpteur, peintre de la Chapelle Sixtine
- Raphaël : maître de l'harmonie et de la beauté idéale

## Révolution scientifique

### Nouvelles découvertes
- Copernic et l'héliocentrisme
- Galilée et l'observation astronomique
- Vésale et l'anatomie moderne
- Développement de la cartographie

### Méthode scientifique
Émergence d'une approche empirique basée sur l'observation et l'expérimentation.

## Transformations religieuses

### Réforme protestante
Martin Luther (1517) remet en question l'autorité papale, déclenchant un mouvement de réforme qui divise la chrétienté.

### Contre-Réforme catholique
L'Église catholique répond par le Concile de Trente (1545-1563) et une rénovation interne.

## Conséquences et héritage

### Impact culturel
- Développement de l'imprimerie (Gutenberg)
- Diffusion de la culture écrite
- Émergence des langues vernaculaires

### Transformations politiques
- Renforcement des monarchies nationales
- Développement de la diplomatie moderne
- Expansion européenne vers les Amériques

La Renaissance constitue une période charnière qui pose les bases de l'Europe moderne et influence durablement la civilisation occidentale.
      ''',
      authorName: 'Dr. Sophie Dubois',
      price: 1800.0,
      isFree: false,
      createdAt: DateTime.now().subtract(const Duration(days: 5)),
    ),
  ];

  /// Données de démonstration pour les cours
  static List<Map<String, dynamic>> get demoCourses => [
    {
      'id': 1,
      'nom': 'Programmation Python Avancée',
      'filiere': 'Informatique',
      'university': 'Université de Kinshasa',
      'professeur': 'Prof. Jean Mukendi',
    },
    {
      'id': 2,
      'nom': 'Analyse Mathématique',
      'filiere': 'Mathématiques',
      'university': 'Université de Lubumbashi',
      'professeur': 'Prof. Marie Kabila',
    },
    {
      'id': 3,
      'nom': 'Histoire Contemporaine',
      'filiere': 'Histoire',
      'university': 'Université de Kisangani',
      'professeur': 'Dr. Pierre Tshisekedi',
    },
  ];

  /// Données de démonstration pour les sessions audio
  static List<Map<String, dynamic>> get demoAudioSessions => [
    {
      'id': 1,
      'course': {
        'nom': 'Programmation Python',
        'filiere': 'Informatique',
        'university': 'Université de Kinshasa',
      },
      'professeur': 'Prof. Jean Mukendi',
      'date': DateTime.now().subtract(const Duration(days: 2)).toIso8601String(),
      'audio_info': {
        'success': true,
        'file_size_mb': 15.2,
        'estimated_duration_minutes': 45,
        'quality_info': {'quality': 'Bonne'},
      },
      'related_summaries': [
        {'id': 1, 'title': 'Résumé Python - Variables et Types'}
      ],
    },
    {
      'id': 2,
      'course': {
        'nom': 'Analyse Mathématique',
        'filiere': 'Mathématiques',
        'university': 'Université de Lubumbashi',
      },
      'professeur': 'Prof. Marie Kabila',
      'date': DateTime.now().subtract(const Duration(days: 1)).toIso8601String(),
      'audio_info': {
        'success': true,
        'file_size_mb': 22.8,
        'estimated_duration_minutes': 60,
        'quality_info': {'quality': 'Excellente'},
      },
      'related_summaries': [],
    },
  ];

  /// Statistiques de démonstration pour l'audio
  static Map<String, dynamic> get demoAudioStats => {
    'stats': {
      'total_sessions': 12,
      'processed_sessions': 8,
      'pending_sessions': 4,
      'total_audio_size_mb': 156.7,
      'processing_rate': 67,
    }
  };

  /// Profil utilisateur de démonstration
  static Map<String, dynamic> get demoUserProfile => {
    'username': 'demo_user',
    'email': 'demo@resumeplus.com',
    'profile': {
      'groupe': 'ETUDIANT',
    }
  };

  /// Données de démonstration pour les achats
  static List<Map<String, dynamic>> get demoPurchases => [
    {
      'id': 1,
      'summary_id': 1,
      'summary_title': 'Résumé IA - Programmation Python',
      'price': 0.0,
      'purchase_date': DateTime.now().subtract(const Duration(days: 1)).toIso8601String(),
      'status': 'completed',
    },
    {
      'id': 2,
      'summary_id': 3,
      'summary_title': 'Histoire - La Renaissance Européenne',
      'price': 1800.0,
      'purchase_date': DateTime.now().subtract(const Duration(days: 5)).toIso8601String(),
      'status': 'completed',
    },
  ];

  /// Vérifie si on est en mode démo (pas de token d'authentification)
  static bool isDemoMode(String? token) {
    return token == null || token.isEmpty;
  }
}