import 'package:flutter/material.dart';
import 'package:resume_plus_clean/models/universite.dart';
import 'package:resume_plus_clean/models/filiere.dart';
import 'package:resume_plus_clean/models/promotion.dart';
import 'package:resume_plus_clean/services/api_service.dart';

class LinkedDropdowns extends StatefulWidget {
  final ValueChanged<Map<String, dynamic>> onSelectionChanged;
  final ApiService apiService;
  
  const LinkedDropdowns({
    Key? key,
    required this.onSelectionChanged,
    required this.apiService,
  }) : super(key: key);

  @override
  _LinkedDropdownsState createState() => _LinkedDropdownsState();
}

class _LinkedDropdownsState extends State<LinkedDropdowns> {
  List<Universite> _universites = [];
  List<Filiere> _filieres = [];
  List<Promotion> _promotions = [];
  
  Universite? _selectedUniversite;
  Filiere? _selectedFiliere;
  Promotion? _selectedPromotion;
  
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    try {
      if (!mounted) return;
      setState(() {
        _isLoading = true;
        _error = null;
      });
      
      final universites = await widget.apiService.getUniversites();
      
      if (!mounted) return;
      setState(() {
        _universites = universites;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Erreur lors du chargement des données';
        _isLoading = false;
      });
    }
  }

  Future<void> _onUniversiteChanged(Universite? universite) async {
    if (universite == null || !mounted) return;
    
    setState(() {
      _selectedUniversite = universite;
      _selectedFiliere = null;
      _selectedPromotion = null;
      _filieres = [];
      _promotions = [];
    });

    try {
      final filieres = await widget.apiService.getFilieresByUniversite(universite.id);
      if (!mounted) return;
      setState(() {
        _filieres = filieres;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Erreur lors du chargement des filières';
      });
    }
    
    _notifyParent();
  }

  Future<void> _onFiliereChanged(Filiere? filiere) async {
    if (filiere == null || !mounted) return;
    
    setState(() {
      _selectedFiliere = filiere;
      _selectedPromotion = null;
      _promotions = [];
    });

    try {
      final promotions = await widget.apiService.getPromotionsByFiliere(filiere.id);
      if (!mounted) return;
      setState(() {
        _promotions = promotions;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Erreur lors du chargement des promotions';
      });
    }
    
    _notifyParent();
  }

  void _onPromotionChanged(Promotion? promotion) {
    if (!mounted) return;
    setState(() {
      _selectedPromotion = promotion;
    });
    _notifyParent();
  }

  void _notifyParent() {
    widget.onSelectionChanged({
      'universite': _selectedUniversite,
      'filiere': _selectedFiliere,
      'promotion': _selectedPromotion,
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Column(
        children: [
          Text(_error!, style: const TextStyle(color: Colors.red)),
          TextButton(
            onPressed: _loadInitialData,
            child: const Text('Réessayer'),
          ),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Sélecteur d'université
        DropdownButtonFormField<Universite>(
          decoration: const InputDecoration(
            labelText: 'Université',
            border: OutlineInputBorder(),
          ),
          value: _selectedUniversite,
          items: _universites
              .map((univ) => DropdownMenuItem(
                    value: univ,
                    child: Text(univ.nom),
                  ))
              .toList(),
          onChanged: _onUniversiteChanged,
          validator: (value) =>
              value == null ? 'Veuillez sélectionner une université' : null,
        ),
        const SizedBox(height: 16),
        
        // Sélecteur de filière
        DropdownButtonFormField<Filiere>(
          decoration: const InputDecoration(
            labelText: 'Filière',
            border: OutlineInputBorder(),
          ),
          value: _selectedFiliere,
          items: _filieres
              .map((filiere) => DropdownMenuItem(
                    value: filiere,
                    child: Text(filiere.nom),
                  ))
              .toList(),
          onChanged: _selectedUniversite != null ? _onFiliereChanged : null,
          validator: (value) =>
              value == null ? 'Veuillez sélectionner une filière' : null,
          disabledHint: const Text('Sélectionnez d\'abord une université'),
        ),
        const SizedBox(height: 16),
        
        // Sélecteur de promotion
        DropdownButtonFormField<Promotion>(
          decoration: const InputDecoration(
            labelText: 'Promotion',
            border: OutlineInputBorder(),
          ),
          value: _selectedPromotion,
          items: _promotions
              .map((promo) => DropdownMenuItem(
                    value: promo,
                    child: Text('${promo.nom} - ${promo.annee}'),
                  ))
              .toList(),
          onChanged: _selectedFiliere != null ? _onPromotionChanged : null,
          validator: (value) =>
              value == null ? 'Veuillez sélectionner une promotion' : null,
          disabledHint: const Text('Sélectionnez d\'abord une filière'),
        ),
      ],
    );
  }
}
