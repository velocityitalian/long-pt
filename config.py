"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY PORTUGUESE"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "PORTUGUESE"
HANDLE = "@velocityportuguese"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'pt',
 'name': 'Portuguese',
 'native_name': 'Português',
 'history_key': 'portuguese',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'pt-PT-RaquelNeural',
 'native_fallback_voice': 'pt-PT-DuarteNeural',
 'native_engine': 'edge',
 'native_lang_code': 'pt',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'PORTUGUÊS',
 'translit_label': 'SAY IT LIKE',
 'flag': 'pt',
 'greeting': 'Olá!',
 'encouragement': 'Excelente!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÂÃÀÇÉÊÍÓÔÕÚáâãàçéêíóôõú'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Motivação',
 'Love': 'Amor',
 'Success': 'Sucesso',
 'Wisdom': 'Sabedoria',
 'Happiness': 'Felicidade',
 'Self Improvement': 'Autoaperfeiçoamento',
 'Gratitude': 'Gratidão',
 'Friendship': 'Amizade',
 'Hope': 'Esperança',
 'Creativity': 'Criatividade',
 'Inner Peace': 'Paz Interior',
 'Confidence': 'Confiança',
 'Perseverance': 'Perseverança',
 'Inspiration': 'Inspiração',
 'Positive Life': 'Vida Positiva',
 'Courage': 'Coragem',
 'Kindness': 'Bondade',
 'Patience': 'Paciência',
 'Forgiveness': 'Perdão',
 'Strength': 'Força',
 'Joy': 'Alegria',
 'Balance': 'Equilíbrio',
 'Growth': 'Crescimento',
 'Purpose': 'Propósito',
 'Mindfulness': 'Atenção Plena',
 'Travel & Airport': 'Viagem e Aeroporto',
 'Ordering Food & Dining': 'Pedir Comida e Refeições',
 'Shopping & Prices': 'Compras e Preços',
 'Asking for Directions': 'Pedir Informações de Direção',
 'Hotel & Accommodation': 'Hotel e Acomodação',
 'Daily Routine': 'Rotina Diária',
 'Meeting People & Greetings': 'Conhecer Pessoas e Cumprimentos',
 'Emergency & Health': 'Emergência e Saúde',
 'Public Transportation': 'Transporte Público',
 'Work & Office': 'Trabalho e Escritório',
 'Weather & Small Talk': 'Tempo e Conversa Fiada',
 'Coffee Shop & Bakery': 'Cafeteria e Padaria',
 'Family & Home': 'Família e Casa',
 'Hobbies & Free Time': 'Hobbies e Tempo Livre',
 'Dating & Romance': 'Namoro e Romance',
 'Phone Calls & Messages': 'Chamadas Telefônicas e Mensagens',
 'Banking & Money': 'Banca e Dinheiro',
 'Doctor & Pharmacy': 'Médico e Farmácia',
 'Sports & Fitness': 'Esportes e Fitness',
 'Celebrations & Parties': 'Celebrações e Festas',
 'Feelings & Emotions': 'Sentimentos e Emoções',
 'Agreeing & Disagreeing': 'Concordar e Discordar',
 'Making Plans': 'Fazer Planos',
 'Common Native Slang': 'Gírias Nativas Comuns',
 'Cultural Traditions': 'Tradições Culturais'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnportuguese',
 '#portugueselessons',
 '#portugueseforbeginners',
 '#languagelearning',
 '#portuguesevocabulary',
 '#velocityportuguese',
 '#dailyportuguese',
 '#portuguese',
 '#learnlanguages',
 '#speakportuguese']
# ==== HASHTAGS END ====
