"""
Service Deepgram pour la transcription audio
Utilise l'API Deepgram pour convertir les fichiers audio en texte
"""

import os
import json
import logging
import requests
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)

class DeepgramService:
    """Service pour la transcription audio via Deepgram API"""
    
    def __init__(self):
        # Utiliser decouple pour lire depuis .env
        self.api_key = config('DEEPGRAM_API_KEY', default='')
        self.base_url = 'https://api.deepgram.com/v1/listen'
        
        if not self.api_key:
            logger.warning("⚠️ DEEPGRAM_API_KEY non configurée")
    
    def is_configured(self):
        """Vérifie si le service est correctement configuré"""
        return bool(self.api_key)
    
    def transcribe_file(self, file_path, language='fr'):
        """
        Transcrit un fichier audio en texte
        
        Args:
            file_path: Chemin vers le fichier audio
            language: Code de langue (fr, en, etc.)
            
        Returns:
            dict: {
                'success': bool,
                'transcript': str,
                'confidence': float,
                'words': list,
                'error': str (si erreur)
            }
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Service Deepgram non configuré (clé API manquante)'
            }
        
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'Fichier non trouvé: {file_path}'
            }
        
        try:
            logger.info(f"🎤 Transcription Deepgram: {file_path}")
            
            # Déterminer le type MIME
            mime_type = self._get_mime_type(file_path)
            
            # Paramètres de l'API Deepgram
            params = {
                'model': 'nova-2',  # Modèle le plus récent et précis
                'language': language,
                'punctuate': 'true',
                'paragraphs': 'true',
                'smart_format': 'true',
                'diarize': 'false',  # Pas de détection de locuteurs pour l'instant
            }
            
            # Headers
            headers = {
                'Authorization': f'Token {self.api_key}',
                'Content-Type': mime_type,
            }
            
            # Lire le fichier audio
            with open(file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Timeout adaptatif selon la taille du fichier
            # Base: 5 min + 2 min par tranche de 50MB (max 30 min)
            file_size_mb = len(audio_data) / (1024 * 1024)
            adaptive_timeout = min(1800, 300 + int(file_size_mb / 50) * 120)
            logger.info(
                f"📡 Deepgram: envoi de {file_size_mb:.1f}MB, "
                f"timeout adaptatif: {adaptive_timeout}s ({adaptive_timeout//60}min)"
            )
            
            # Appel à l'API Deepgram
            response = requests.post(
                self.base_url,
                params=params,
                headers=headers,
                data=audio_data,
                timeout=adaptive_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extraire la transcription
                transcript = self._extract_transcript(result)
                confidence = self._extract_confidence(result)
                words = self._extract_words(result)
                
                logger.info(f"✅ Transcription réussie: {len(transcript)} caractères")
                
                return {
                    'success': True,
                    'transcript': transcript,
                    'confidence': confidence,
                    'words': words,
                    'raw_response': result
                }
            else:
                error_msg = f"Erreur API Deepgram: {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0
            return {
                'success': False,
                'error': f'Timeout Deepgram après {adaptive_timeout}s pour fichier de {file_size_mb:.1f}MB. Le fichier est peut-être trop volumineux.'
            }
        except Exception as e:
            logger.error(f"❌ Erreur transcription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def transcribe_bytes(self, audio_bytes, mime_type='audio/wav', language='fr'):
        """
        Transcrit des bytes audio en texte
        
        Args:
            audio_bytes: Données audio en bytes
            mime_type: Type MIME de l'audio
            language: Code de langue
            
        Returns:
            dict: Résultat de la transcription
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Service Deepgram non configuré'
            }
        
        try:
            logger.info(f"🎤 Transcription Deepgram (bytes): {len(audio_bytes)} bytes")
            
            params = {
                'model': 'nova-2',
                'language': language,
                'punctuate': 'true',
                'paragraphs': 'true',
                'smart_format': 'true',
            }
            
            headers = {
                'Authorization': f'Token {self.api_key}',
                'Content-Type': mime_type,
            }
            
            # Timeout adaptatif selon la taille des bytes
            bytes_size_mb = len(audio_bytes) / (1024 * 1024)
            adaptive_timeout = min(1800, 300 + int(bytes_size_mb / 50) * 120)
            logger.info(f"📡 Deepgram bytes: {bytes_size_mb:.1f}MB, timeout: {adaptive_timeout}s")
            
            response = requests.post(
                self.base_url,
                params=params,
                headers=headers,
                data=audio_bytes,
                timeout=adaptive_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                transcript = self._extract_transcript(result)
                confidence = self._extract_confidence(result)
                
                return {
                    'success': True,
                    'transcript': transcript,
                    'confidence': confidence,
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur API: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_mime_type(self, file_path):
        """Détermine le type MIME basé sur l'extension"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm',
            '.flac': 'audio/flac',
        }
        return mime_types.get(ext, 'audio/wav')
    
    def _extract_transcript(self, result):
        """Extrait le texte transcrit du résultat Deepgram"""
        try:
            channels = result.get('results', {}).get('channels', [])
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('transcript', '')
        except Exception as e:
            logger.error(f"Erreur extraction transcript: {e}")
        return ''
    
    def _extract_confidence(self, result):
        """Extrait le score de confiance"""
        try:
            channels = result.get('results', {}).get('channels', [])
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('confidence', 0.0)
        except Exception:
            pass
        return 0.0
    
    def _extract_words(self, result):
        """Extrait les mots avec leurs timestamps"""
        try:
            channels = result.get('results', {}).get('channels', [])
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('words', [])
        except Exception:
            pass
        return []


# Instance globale du service
deepgram_service = DeepgramService()
