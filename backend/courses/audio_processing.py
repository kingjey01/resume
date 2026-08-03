"""
Module de traitement audio pour Resume+
Gère la transcription et génération de résumés en 2 étapes:
  - Étape 1: Transcription audio → texte via Deepgram (stocké dans Transcription)
  - Étape 2: Génération de résumé intelligent à partir de la transcription (stocké dans Summary)
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Session, Summary, Course, Transcription
from .deepgram_service import deepgram_service
from .deepseek_service import deepseek_service
import mimetypes

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Classe principale pour le traitement audio"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.webm']
        self.max_file_size = 100 * 1024 * 1024  # 100MB
    
    def get_audio_info(self, session_id):
        """Récupère les informations détaillées d'un fichier audio"""
        try:
            session = Session.objects.get(id=session_id)
            
            if not session.audio_file:
                return {
                    'success': False,
                    'error': 'Aucun fichier audio'
                }
            
            file_path = session.audio_file.path if hasattr(session.audio_file, 'path') else None
            file_url = session.audio_file.url
            file_size = session.audio_file.size if hasattr(session.audio_file, 'size') else 0
            
            # Déterminer le type MIME
            mime_type, _ = mimetypes.guess_type(session.audio_file.name)
            
            # Informations de base
            info = {
                'success': True,
                'session_id': session_id,
                'file_name': session.audio_file.name,
                'file_url': file_url,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2) if file_size else 0,
                'mime_type': mime_type,
                'is_supported': self._is_supported_format(session.audio_file.name),
                'course_name': session.course.nom,
                'professor': session.professeur,
                'recorded_date': session.date,
                'created_at': session.created_at
            }
            
            # Essayer d'obtenir la durée si possible
            try:
                duration = self._get_audio_duration(file_path) if file_path else None
                if duration:
                    info['duration_seconds'] = duration
                    info['duration_formatted'] = self._format_duration(duration)
            except Exception as e:
                logger.warning(f"Impossible d'obtenir la durée audio: {e}")
                info['duration_seconds'] = None
                info['duration_formatted'] = 'Inconnue'
            
            return info
            
        except Session.DoesNotExist:
            return {
                'success': False,
                'error': 'Session non trouvée'
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos audio: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_supported_format(self, filename):
        """Vérifie si le format audio est supporté"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.supported_formats
    
    def _get_audio_duration(self, file_path):
        """Obtient la durée d'un fichier audio"""
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        
        # Estimation basée sur la taille du fichier
        try:
            file_size = os.path.getsize(file_path)
            estimated_minutes = file_size / (1024 * 1024)
            return estimated_minutes * 60
        except:
            return None
    
    def _format_duration(self, seconds):
        """Formate la durée en format lisible"""
        if not seconds:
            return "Inconnue"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def process_audio_session(self, session_id, summary_title=None, summary_price=0.0, author_user=None):
        """
        Traite une session audio en 2 étapes:
        - Étape 1: Transcription audio → texte via Deepgram (stocké dans Transcription)
        - Étape 2: Génération de résumé intelligent (stocké dans Summary)
        
        Args:
            session_id: ID de la session audio
            summary_title: Titre personnalisé du résumé (optionnel)
            summary_price: Prix du résumé (défaut: 0.0 = gratuit)
            author_user: Utilisateur auteur du résumé (optionnel)
        """
        try:
            session = Session.objects.get(id=session_id)
            
            if not session.audio_file:
                return {
                    'success': False,
                    'error': 'Aucun fichier audio à traiter'
                }
            
            # ========================================
            # ÉTAPE 1: TRANSCRIPTION (Deepgram → Transcription)
            # ========================================
            transcription = self._step1_transcribe_audio(session)
            
            if not transcription:
                return {
                    'success': False,
                    'error': 'Échec de la transcription audio'
                }
            
            logger.info(f"✅ ÉTAPE 1 TERMINÉE: Transcription ID {transcription.id} créée")
            
            # ========================================
            # ÉTAPE 2: GÉNÉRATION DU RÉSUMÉ (Transcription → Summary)
            # ========================================
            summary_result = self._step2_generate_summary(
                transcription=transcription,
                session=session,
                summary_title=summary_title,
                summary_price=summary_price,
                author_user=author_user
            )

            summary = summary_result.get('summary') if isinstance(summary_result, dict) else summary_result
            generated_by_ai = summary_result.get('generated_by_ai', False) if isinstance(summary_result, dict) else False

            if not summary:
                return {
                    'success': False,
                    'error': 'Échec de la génération du résumé'
                }
            
            logger.info(f"✅ ÉTAPE 2 TERMINÉE: Résumé ID {summary.id} créé")
            
            return {
                'success': True,
                'message': 'Traitement complet: Transcription + Résumé générés',
                'transcription_id': transcription.id,
                'summary_id': summary.id,
                'generated_by_ai': generated_by_ai,
                'transcript': transcription.texte_transcription[:500] + '...' if len(transcription.texte_transcription) > 500 else transcription.texte_transcription,
                'confidence': transcription.confidence
            }
            
        except Session.DoesNotExist:
            return {
                'success': False,
                'error': 'Session non trouvée'
            }
        except Exception as e:
            logger.error(f"Erreur lors du traitement audio: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _step1_transcribe_audio(self, session):
        """
        ÉTAPE 1: Transcription de l'audio via Deepgram
        Stocke le résultat dans la table Transcription
        """
        # Logging pour diagnostic
        logger.info(f"🔍 DIAGNOSTIC - Début étape 1 transcription")
        logger.info(f"🔍 Session ID: {session.id}")
        logger.info(f"🔍 Session date: {session.date}")
        logger.info(f"🔍 Session course: {session.course}")
        logger.info(f"🔍 Audio file: {session.audio_file}")
        
        # Vérifier si une transcription existe déjà
        existing_transcription = Transcription.objects.filter(
            session=session,
            status='completed'
        ).first()
        
        if existing_transcription:
            logger.info(f"Transcription existante trouvée: ID {existing_transcription.id}")
            return existing_transcription
        
        # Créer une nouvelle transcription en statut "processing"
        logger.info(f"🔍 Création transcription avec session_id={session.id}")
        transcription = Transcription.objects.create(
            session=session,
            texte_transcription='',
            langue='fr',
            duree_audio=0.0,
            confidence=0.0,
            status='processing'
        )
        logger.info(f"🔍 Transcription créée: ID={transcription.id}, created_at={transcription.created_at}")
        
        try:
            transcript_text = None
            confidence = 0.0
            duration = 0.0
            
            # Utiliser Deepgram pour la transcription
            if deepgram_service.is_configured():
                logger.info(f"🎤 Transcription Deepgram pour session {session.id}")
                
                file_path = session.audio_file.path if hasattr(session.audio_file, 'path') else None
                
                if file_path and os.path.exists(file_path):
                    result = deepgram_service.transcribe_file(file_path, language='fr')
                    
                    if result['success']:
                        transcript_text = result['transcript']
                        confidence = result.get('confidence', 0.0)
                        duration = result.get('duration', 0.0)
                        print(f"✅ Transcription Deepgram réussie (confiance: {confidence:.2%})")
                        logger.info(f"✅ Transcription Deepgram réussie (confiance: {confidence:.2%})")
                    else:
                        logger.warning(f"⚠️ Échec Deepgram: {result['error']}")
                        transcription.error_message = result['error']
                else:
                    logger.warning(f"⚠️ Fichier audio non accessible: {file_path}")
                    transcription.error_message = "Fichier audio non accessible"
            else:
                logger.warning("⚠️ Deepgram non configuré")
                transcription.error_message = "Service Deepgram non configuré"
            
            # Fallback: simulation si Deepgram échoue
            if not transcript_text:
                transcript_text = self._simulate_transcription(session)
                logger.info("📝 Utilisation de la transcription simulée (fallback)")
            
            # Mettre à jour la transcription
            transcription.texte_transcription = transcript_text
            transcription.confidence = confidence
            transcription.duree_audio = duration
            transcription.status = 'completed'
            transcription.save()
            
            return transcription
            
        except Exception as e:
            logger.error(f"❌ Erreur transcription: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.save()
            return None
    
    def _step2_generate_summary(self, transcription, session, summary_title=None, summary_price=0.0, author_user=None):
        """
        ÉTAPE 2: Génération du résumé intelligent à partir de la transcription
        
        Utilise DeepSeek API pour générer un vrai résumé intelligent.
        
        Règles de résumé (appliquées par DeepSeek):
        - Conserver les idées principales
        - Ne pas inventer d'informations
        - Conserver uniquement les idées essentielles
        - Éliminer les répétitions, hésitations et digressions
        - Utiliser un langage simple, professionnel et pédagogique
        - Produire un résumé en paragraphes cohérents
        """
        # Logging pour diagnostic
        logger.info(f"🔍 DIAGNOSTIC - Début étape 2 génération résumé")
        logger.info(f"🔍 Transcription ID: {transcription.id}")
        logger.info(f"🔍 Transcription created_at: {transcription.created_at}")
        logger.info(f"🔍 Session ID: {session.id}")
        logger.info(f"🔍 Session date: {session.date}")
        logger.info(f"🔍 Author user: {author_user}")
        
        # Vérifier si un résumé existe déjà pour cette transcription
        existing_summary = Summary.objects.filter(
            transcription=transcription,
            author_type='ai'
        ).first()
        
        if existing_summary:
            logger.info(f"Résumé existant trouvé: ID {existing_summary.id}")
            return {
                'summary': existing_summary,
                # Impossible de savoir si ce résumé existant a été produit via DeepSeek ou fallback local
                'generated_by_ai': False
            }
        
        try:
            course_name = session.course.nom
            professor = session.professeur
            
            # Vérifier si la date est valide
            if session.date:
                date = session.date.strftime('%d/%m/%Y')
            else:
                date = timezone.now().strftime('%d/%m/%Y')
                logger.warning(f"⚠️ Session {session.id} sans date, utilisation de la date actuelle")
            
            # ========================================
            # UTILISER DEEPSEEK POUR LE RÉSUMÉ INTELLIGENT
            # ========================================
            summary_text = None
            generated_by_ai = False
            
            if deepseek_service.is_configured():
                logger.info(f"🤖 Génération du résumé via DeepSeek API...")
                
                result = deepseek_service.generate_summary(
                    transcription_text=transcription.texte_transcription,
                    course_name=course_name,
                    professor=professor,
                    date=date
                )
                
                if result['success']:
                    summary_text = result['summary']
                    generated_by_ai = True
                    logger.info(f"✅ Résumé DeepSeek généré avec succès")
                else:
                    logger.warning(f"⚠️ Échec DeepSeek: {result['error']}")
            else:
                logger.warning("⚠️ DeepSeek non configuré, utilisation du fallback local")
            
            # Fallback: utiliser le résumé local si DeepSeek échoue
            if not summary_text:
                logger.info("📝 Utilisation du résumé local (fallback)")
                summary_text = self._generate_local_summary(
                    transcription.texte_transcription,
                    session
                )
            
            # Titre du résumé
            final_title = summary_title if summary_title else f"Résumé - {course_name} ({date})"
            final_price = float(summary_price) if summary_price else 0.0
            is_free = final_price == 0.0
            
            # Créer le résumé en base
            logger.info(f"🔍 Création Summary avec:")
            logger.info(f"🔍   - titre: {final_title}")
            logger.info(f"🔍   - course: {session.course}")
            logger.info(f"🔍   - session: {session}")
            logger.info(f"🔍   - transcription: {transcription}")
            logger.info(f"🔍   - author_user: {author_user}")
            
            summary = Summary.objects.create(
                titre=final_title,
                texte_resume=summary_text,
                course=session.course,
                session=session,
                transcription=transcription,
                professeur=session.professeur_fk,
                author_type='ai',
                author_user=author_user,
                prix=final_price,
                is_free=is_free
            )
            
            logger.info(f"🔍 Summary créé: ID={summary.id}, created_at={summary.created_at}")
            return {
                'summary': summary,
                'generated_by_ai': generated_by_ai
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération résumé: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _generate_local_summary(self, transcript_text, session):
        """
        Génère un résumé local (fallback si DeepSeek n'est pas disponible)
        Utilise un traitement basique du texte
        """
        course_name = session.course.nom
        professor = session.professeur
        
        # Vérifier si la date est valide
        if session.date:
            date = session.date.strftime('%d/%m/%Y')
        else:
            date = timezone.now().strftime('%d/%m/%Y')
            logger.warning(f"⚠️ Session {session.id} sans date, utilisation de la date actuelle")
        
        # Nettoyer la transcription
        cleaned_text = self._clean_transcript(transcript_text)
        
        # Extraire les idées principales
        main_ideas = self._extract_main_ideas(cleaned_text)
        
        # Structurer le résumé
        summary = self._structure_summary(
            main_ideas=main_ideas,
            course_name=course_name,
            professor=professor,
            date=date
        )
        
        return summary
    
    def _generate_intelligent_summary(self, transcript_text, session):
        """
        Génère un résumé intelligent à partir de la transcription
        
        Applique les règles:
        - Conserver les idées principales
        - Ne pas inventer d'informations
        - Éliminer répétitions, hésitations, digressions
        - Langage simple, professionnel, pédagogique
        - Paragraphes cohérents
        """
        course_name = session.course.nom
        professor = session.professeur
        date = session.date.strftime('%d/%m/%Y')
        
        # Nettoyer la transcription
        cleaned_text = self._clean_transcript(transcript_text)
        
        # Extraire les idées principales
        main_ideas = self._extract_main_ideas(cleaned_text)
        
        # Structurer le résumé
        summary = self._structure_summary(
            main_ideas=main_ideas,
            course_name=course_name,
            professor=professor,
            date=date
        )
        
        return summary
    
    def _clean_transcript(self, text):
        """
        Nettoie la transcription:
        - Supprime les hésitations (euh, hum, etc.)
        - Supprime les répétitions consécutives
        - Normalise les espaces et la ponctuation
        """
        if not text:
            return ""
        
        # Supprimer les hésitations courantes
        hesitations = [
            r'\b(euh|hum|hmm|ah|oh|ben|bah|hein|quoi)\b',
            r'\.\.\.',
            r'…',
        ]
        
        cleaned = text
        for pattern in hesitations:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Supprimer les répétitions de mots consécutifs
        cleaned = re.sub(r'\b(\w+)(\s+\1)+\b', r'\1', cleaned, flags=re.IGNORECASE)
        
        # Normaliser les espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Normaliser la ponctuation
        cleaned = re.sub(r'\s+([.,;:!?])', r'\1', cleaned)
        cleaned = re.sub(r'([.,;:!?])([A-Za-zÀ-ÿ])', r'\1 \2', cleaned)
        
        return cleaned.strip()
    
    def _extract_main_ideas(self, text):
        """
        Extrait les idées principales du texte
        Divise en paragraphes logiques
        """
        if not text:
            return []
        
        # Diviser en phrases
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        # Regrouper les phrases en paragraphes thématiques
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            current_paragraph.append(sentence)
            
            # Créer un nouveau paragraphe tous les 3-4 phrases
            if len(current_paragraph) >= 3:
                paragraphs.append('. '.join(current_paragraph) + '.')
                current_paragraph = []
        
        # Ajouter le dernier paragraphe
        if current_paragraph:
            paragraphs.append('. '.join(current_paragraph) + '.')
        
        return paragraphs
    
    def _structure_summary(self, main_ideas, course_name, professor, date):
        """
        Structure le résumé final de manière professionnelle et pédagogique.
        Supprime les symboles inutiles et privilégie une mise en page claire.
        """
        # En-tête du résumé plus sobre
        header = f"""RESUME DE COURS : {course_name.upper()}
Professeur : {professor}
Date : {date}

"""
        
        # Corps du résumé
        if main_ideas:
            body = "DEVELOPPEMENT ET NOTIONS CLES\n\n"
            
            for idea in main_ideas:
                # S'assurer que l'idée ne commence pas par des symboles parasites
                clean_idea = re.sub(r'^[#*-\s]+', '', idea).strip()
                if clean_idea:
                    body += f"• {clean_idea}\n\n"
        else:
            body = "Le contenu de ce cours n'a pas pu être structuré automatiquement.\n\n"
        
        # Pied de page discret
        footer = """
Ce document est un résumé pédagogique généré à partir de l'enregistrement de la séance.
Il a été conçu pour faciliter la révision et la compréhension des points essentiels.
"""
        
        return header + body + footer
    
    def _simulate_transcription(self, session):
        """Simule une transcription audio (fallback)"""
        course_name = session.course.nom
        professor = session.professeur
        
        transcript = f"""Bonjour, je suis {professor} et aujourd'hui nous allons étudier {course_name}.

Dans cette séance, nous aborderons les concepts fondamentaux de ce sujet.
Nous verrons d'abord les définitions de base, puis nous approfondirons avec des exemples pratiques.

Les points clés à retenir sont:
- La compréhension des concepts théoriques
- L'application pratique des connaissances
- Les exercices et cas d'usage

N'hésitez pas à prendre des notes et à poser des questions.
Nous ferons un récapitulatif à la fin de la séance.

[Transcription automatique générée - Version démo]"""
        
        return transcript
    
    def batch_process_sessions(self, session_ids):
        """Traite plusieurs sessions en lot"""
        results = []
        
        for session_id in session_ids:
            try:
                result = self.process_audio_session(session_id)
                results.append({
                    'session_id': session_id,
                    'success': result['success'],
                    'message': result.get('message', result.get('error')),
                    'summary_id': result.get('summary_id')
                })
            except Exception as e:
                results.append({
                    'session_id': session_id,
                    'success': False,
                    'message': str(e)
                })
        
        return results
    
    def auto_process_pending_sessions(self):
        """Traite automatiquement toutes les sessions en attente"""
        try:
            pending_sessions = Session.objects.filter(
                audio_file__isnull=False
            ).exclude(
                summaries__author_type='ai'
            )
            
            session_ids = list(pending_sessions.values_list('id', flat=True))
            
            if not session_ids:
                return {
                    'success': True,
                    'processed_count': 0,
                    'message': 'Aucune session en attente'
                }
            
            results = self.batch_process_sessions(session_ids)
            processed_count = sum(1 for r in results if r['success'])
            
            return {
                'success': True,
                'processed_count': processed_count,
                'total_sessions': len(session_ids),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement automatique: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_processing_stats(self):
        """Récupère les statistiques de traitement"""
        try:
            total_sessions = Session.objects.filter(audio_file__isnull=False).count()
            processed_sessions = Session.objects.filter(
                audio_file__isnull=False,
                summaries__author_type='ai'
            ).distinct().count()
            
            pending_sessions = total_sessions - processed_sessions
            
            course_stats = {}
            for session in Session.objects.filter(audio_file__isnull=False).select_related('course'):
                course_name = session.course.nom
                if course_name not in course_stats:
                    course_stats[course_name] = {'total': 0, 'processed': 0}
                course_stats[course_name]['total'] += 1
                
                if session.summaries.filter(author_type='ai').exists():
                    course_stats[course_name]['processed'] += 1
            
            return {
                'total_audio_sessions': total_sessions,
                'processed_sessions': processed_sessions,
                'pending_sessions': pending_sessions,
                'processing_rate': round((processed_sessions / total_sessions * 100), 2) if total_sessions > 0 else 0,
                'course_breakdown': course_stats
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return {'error': str(e)}
    
    def cleanup_old_audio_files(self, days_old=30):
        """Nettoie les anciens fichiers audio"""
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            
            old_sessions = Session.objects.filter(
                audio_file__isnull=False,
                created_at__lt=cutoff_date
            )
            
            cleaned_count = 0
            for session in old_sessions:
                try:
                    if session.audio_file and hasattr(session.audio_file, 'path'):
                        file_path = session.audio_file.path
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier pour la session {session.id}: {e}")
            
            return {
                'success': True,
                'message': f'{cleaned_count} fichiers audio supprimés',
                'cleaned_count': cleaned_count
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Instance globale du processeur audio
audio_processor = AudioProcessor()
