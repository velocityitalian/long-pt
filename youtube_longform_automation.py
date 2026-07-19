"""
YouTube Long-Form Video Automation - Bilingual English/Portuguese Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Portuguese translations
CATEGORIES_PORTUGUESE = {
    "Motivation": "Motivação",
    "Love": "Amor",
    "Success": "Sucesso",
    "Wisdom": "Sabedoria",
    "Happiness": "Felicidade",
    "Self Improvement": "Autoaperfeiçoamento",
    "Gratitude": "Gratidão",
    "Friendship": "Amizade",
    "Hope": "Esperança",
    "Creativity": "Criatividade",
    "Inner Peace": "Paz Interior",
    "Confidence": "Confiança",
    "Perseverance": "Perseverança",
    "Inspiration": "Inspiração",
    "Positive Life": "Vida Positiva",
    "Courage": "Coragem",
    "Kindness": "Bondade",
    "Patience": "Paciência",
    "Forgiveness": "Perdão",
    "Strength": "Força",
    "Joy": "Alegria",
    "Balance": "Equilíbrio",
    "Growth": "Crescimento",
    "Purpose": "Propósito",
    "Mindfulness": "Atenção Plena",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "pt-PT-RaquelNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "portuguese": phrase["portuguese"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_portuguese = CATEGORIES_PORTUGUESE[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Portuguese.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - STRICTLY ENFORCE:
The "english" field must contain PURE ENGLISH words only. ZERO Portuguese/Special Characters.
The "portuguese" field contains the Portuguese translation in Portuguese.
The "pronunciation" field is phonetic English spelling.

WRONG (mixed language): {{"english": "Acredite em yourself, believe in yourself", ...}}
WRONG (Portuguese in english): {{"english": "Follow your sonhos and success will come", ...}}
CORRECT: {{"english": "Make your dreams come true, believe in yourself.", "portuguese": "Realize seus sonhos, acredite em si mesmo.", "pronunciation": "re-a-lee-ze se-oos so-nhos, a-cre-dee-te em see meys-mo."}}

The english field MUST be 100% English words only. NO Portuguese words allowed.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Portuguese) with commas for natural pauses
2. Portuguese translation (Portuguese only)
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "portuguese": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a viral Portuguese teacher. CRITICAL: The 'english' field must contain PURE ENGLISH words ONLY. NO Portuguese in english field. Portuguese goes in the 'portuguese' field. This is strictly enforced."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "portuguese": "Acredite em si mesmo.", "pronunciation": "ah-cre-djee-tche em see meys-mo."},
            {"english": "You are capable of amazing things.", "portuguese": "Você é capaz de coisas incríveis.", "pronunciation": "vo-seh eh ka-paz de koy-zas in-cree-veys."},
            {"english": "Dream big, start small.", "portuguese": "Sonhe grande, comece pequeno.", "pronunciation": "so-nye gran-de, ko-me-se pe-ke-no."},
            {"english": "Your future is created by your actions.", "portuguese": "Seu futuro é criado pelas suas ações.", "pronunciation": "sew fu-tu-ro eh cree-a-do pe-las su-as a-soys."},
            {"english": "Never give up on your dreams.", "portuguese": "Nunca desista dos seus sonhos.", "pronunciation": "noon-ka de-zee-sta do sews so-nyohs."},
            {"english": "Small steps lead to big changes.", "portuguese": "Pequenos passos levam a grandes mudanças.", "pronunciation": "pe-ke-nos pa-sos le-vam a gran-des mu-dan-sas."},
            {"english": "You are stronger than you think.", "portuguese": "Você é mais forte do que pensa.", "pronunciation": "vo-seh eh meys for-te do ke pen-sa."},
        ],
        "Love": [
            {"english": "Love yourself first.", "portuguese": "Ame-se primeiro.", "pronunciation": "ah-me-se pree-mei-ro."},
            {"english": "Love makes everything possible.", "portuguese": "O amor torna tudo possível.", "pronunciation": "o a-mor tor-na tu-do po-see-vel."},
            {"english": "My heart beats for you.", "portuguese": "Meu coração bate por você.", "pronunciation": "mew ko-ra-sao ba-te por vo-se."},
            {"english": "You are my everything.", "portuguese": "Você é meu tudo.", "pronunciation": "vo-seh eh mew tu-do."},
            {"english": "Together forever, hand in hand.", "portuguese": "Juntos para sempre, de mãos dadas.", "pronunciation": "joon-tos pa-ra sem-pre, de mows da-das."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "portuguese": "O sucesso vem do trabalho duro.", "pronunciation": "o su-se-so vem do tra-ba-lyo du-ro."},
            {"english": "Keep going, you're getting there.", "portuguese": "Continue, você está chegando lá.", "pronunciation": "kon-ti-nu-e, vo-seh es-ta she-gan-do la."},
            {"english": "Winners never quit.", "portuguese": "Vencedores nunca desistem.", "pronunciation": "ven-se-do-res noon-ka dee-zes-tem."},
            {"english": "Your effort will pay off.", "portuguese": "Seu esforço vai valer a pena.", "pronunciation": "sew es-for-so vai va-ler a pe-na."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "portuguese": "Conhecimento é poder.", "pronunciation": "ko-nye-se-men-to eh po-der."},
            {"english": "Learn from yesterday, live for today.", "portuguese": "Aprenda com ontem, viva para hoje.", "pronunciation": "a-pren-da com on-tem, vee-va pa-ra o-je."},
            {"english": "Think before you act.", "portuguese": "Pense antes de agir.", "pronunciation": "pen-se an-tes de a-jeer."},
            {"english": "Experience is the best teacher.", "portuguese": "A experiência é a melhor professora.", "pronunciation": "a ex-pe-ree-en-see-a eh a me-lyor pro-fe-so-ra."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "portuguese": "Felicidade é uma escolha.", "pronunciation": "fe-lee-see-da-de eh oo-ma es-ko-lya."},
            {"english": "Find joy in the little things.", "portuguese": "Encontre alegria nas pequenas coisas.", "pronunciation": "en-con-tre a-le-gree-a nas pe-ke-nas koy-zas."},
            {"english": "Smile, it makes others happy.", "portuguese": "Sorria, isso faz os outros felizes.", "pronunciation": "so-ree-a, ee-so faz os ow-tros fe-lee-zes."},
            {"english": "Today is a gift.", "portuguese": "Hoje é um presente.", "pronunciation": "o-je eh oom pre-sen-te."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "portuguese": "Seja melhor do que ontem.", "pronunciation": "se-ja me-lyor do ke on-tem."},
            {"english": "Grow through what you go through.", "portuguese": "Cresça através do que você passa.", "pronunciation": "cres-sa a-tra-ves do ke vo-se pa-sa."},
            {"english": "Invest in yourself daily.", "portuguese": "Invista em si mesmo diariamente.", "pronunciation": "in-vees-ta em see meys-mo dee-a-ree-a-men-te."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "portuguese": "Obrigado por tudo.", "pronunciation": "o-bree-ga-do por tu-do."},
            {"english": "I appreciate your help.", "portuguese": "Agradeço pela sua ajuda.", "pronunciation": "a-gra-de-so pe-la su-a a-ju-da."},
            {"english": "Grateful for this moment.", "portuguese": "Grato por este momento.", "pronunciation": "gra-to por es-te mo-men-to."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "portuguese": "Amigos para sempre, não importa o quê.", "pronunciation": "a-mee-gos pa-ra sem-pre, nao im-por-ta o keh."},
            {"english": "You are my best friend.", "portuguese": "Você é meu melhor amigo.", "pronunciation": "vo-seh eh mew me-lyor a-mee-go."},
            {"english": "True friends stick together.", "portuguese": "Verdadeiros amigos ficam juntos.", "pronunciation": "ver-da-dey-ros a-mee-gos fee-cam joon-tos."},
        ],
        "Hope": [
            {"english": "There is always hope.", "portuguese": "Sempre há esperança.", "pronunciation": "sem-pre a es-pe-ran-sa."},
            {"english": "Better days are coming.", "portuguese": "Dias melhores estão chegando.", "pronunciation": "dee-as me-lyo-res es-tao she-gan-do."},
            {"english": "Keep faith, keep going.", "portuguese": "Mantenha a fé, continue.", "pronunciation": "man-ten-ya a feh, kon-ti-nu-e."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "portuguese": "Crie algo bonito hoje.", "pronunciation": "cree-e al-go bo-nee-to o-je."},
            {"english": "Your imagination is unlimited.", "portuguese": "Sua imaginação é ilimitada.", "pronunciation": "su-a e-ma-gee-na-sao eh ee-lee-mee-ta-da."},
            {"english": "Art comes from the heart.", "portuguese": "A arte vem do coração.", "pronunciation": "a ar-te vem do ko-ra-sao."},
            {"english": "Express yourself freely.", "portuguese": "Expresse-se livremente.", "pronunciation": "es-pres-se lee-vre-men-te."},
            {"english": "Innovation starts with curiosity.", "portuguese": "A inovação começa com a curiosidade.", "pronunciation": "a ee-no-va-sao ko-me-sa com a ku-ree-o-zi-da-de."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "portuguese": "Encontre paz dentro de si.", "pronunciation": "en-con-tre paz den-tro de see."},
            {"english": "Breathe, relax, let go.", "portuguese": "Respire, relaxe, deixe ir.", "pronunciation": "res-pee-re, re-la-xe, day-she eer."},
            {"english": "Calm mind, happy heart.", "portuguese": "Mente calma, coração feliz.", "pronunciation": "men-te kal-ma, ko-ra-sao fe-leez."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "portuguese": "Você é suficiente, exatamente como é.", "pronunciation": "vo-seh eh su-fee-see-en-te, e-za-ta-men-te ko-mo eh."},
            {"english": "Stand tall, speak up.", "portuguese": "Fique ereto, fale alto.", "pronunciation": "fee-ke e-re-to, fa-le al-to."},
            {"english": "Believe in your abilities.", "portuguese": "Acredite em suas habilidades.", "pronunciation": "ah-cre-djee-te em su-as a-bee-li-da-des."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "portuguese": "Nunca desista, continue avançando.", "pronunciation": "noon-ka de-zeez-ta, kon-ti-nu-e a-van-san-do."},
            {"english": "Storms make trees take deeper roots.", "portuguese": "As tempestades fazem as árvores criarem raízes mais profundas.", "pronunciation": "as tem-pes-ta-des fa-zem as ar-vo-res cree-a-rem ra-ee-zes meys pro-fun-das."},
            {"english": "Patience and persistence win.", "portuguese": "Paciência e persistência vencem.", "pronunciation": "pa-see-en-see-a e per-sis-ten-see-a ven-sem."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "portuguese": "Deixe sua luz brilhar intensamente.", "pronunciation": "day-she su-a luz bree-lyar in-ten-sa-men-te."},
            {"english": "Inspire others by your actions.", "portuguese": "Inspire outros com suas ações.", "pronunciation": "ins-pee-re ow-tros com su-as a-soys."},
            {"english": "Be the change you want to see.", "portuguese": "Seja a mudança que você quer ver.", "pronunciation": "se-ja a mu-dan-sa ke vo-se kehr vehr."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "portuguese": "Escolha a positividade todos os dias.", "pronunciation": "es-ko-lya a po-zee-tee-vee-da-de to-dos os dee-as."},
            {"english": "Good vibes only.", "portuguese": "Boas vibrações apenas.", "pronunciation": "bo-as vee-bra-soys a-pe-nas."},
            {"english": "Life is what you make it.", "portuguese": "A vida é o que você faz dela.", "pronunciation": "a vee-da eh o ke vo-se faz de-la."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "portuguese": "Seja corajoso, dê o primeiro passo.", "pronunciation": "se-ja ko-ra-jo-zo, de o pree-mei-ro pa-so."},
            {"english": "Courage is not the absence of fear.", "portuguese": "Coragem não é ausência de medo.", "pronunciation": "ko-ra-jem nao eh aw-sen-see-a de me-do."},
            {"english": "Face your fears head on.", "portuguese": "Enfrente seus medos de frente.", "pronunciation": "en-fren-te sews me-dos de fren-te."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "portuguese": "Seja gentil com todos que encontrar.", "pronunciation": "se-ja jen-teel com to-dos ke en-kon-trar."},
            {"english": "Kindness costs nothing, means everything.", "portuguese": "Gentileza não custa nada, significa tudo.", "pronunciation": "jen-tee-le-za nao cus-ta na-da, sig-nee-fee-ca tu-do."},
            {"english": "Spread kindness wherever you go.", "portuguese": "Espalhe gentileza onde quer que vá.", "pronunciation": "es-pa-lye jen-tee-le-za on-de kehr ke va."},
        ],
        "Patience": [
            {"english": "Good things take time.", "portuguese": "Boas coisas levam tempo.", "pronunciation": "bo-as koy-zas le-vam tem-po."},
            {"english": "Wait patiently, trust the process.", "portuguese": "Espere pacientemente, confie no processo.", "pronunciation": "es-pe-re pa-see-en-te-men-te, con-fee-e no pro-se-so."},
            {"english": "Rome wasn't built in a day.", "portuguese": "Roma não foi construída em um dia.", "pronunciation": "ro-ma nao foy con-stru-ee-da em oom dee-a."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "portuguese": "Perdoe e se liberte.", "pronunciation": "per-do-e e se lee-ber-te."},
            {"english": "Let go of grudges, find peace.", "portuguese": "Deixe os rancores de lado, encontre paz.", "pronunciation": "day-she os ran-ko-res de la-do, en-con-tre paz."},
            {"english": "Forgiveness is a gift to yourself.", "portuguese": "O perdão é um presente para si mesmo.", "pronunciation": "o per-dao eh oom pre-sen-te pa-ra see meys-mo."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "portuguese": "Você é mais forte do que imagina.", "pronunciation": "vo-seh eh meys for-te do ke e-ma-zhee-na."},
            {"english": "Inner strength comes from within.", "portuguese": "A força interior vem de dentro.", "pronunciation": "a for-sa in-te-ree-or vem de den-tro."},
            {"english": "Challenges make you stronger.", "portuguese": "Desafios te tornam mais forte.", "pronunciation": "de-za-fee-os te tor-nam meys for-te."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "portuguese": "Encontre alegria em cada momento.", "pronunciation": "en-con-tre a-le-gree-a em ca-da mo-men-to."},
            {"english": "Joy is contagious, spread it.", "portuguese": "A alegria é contagiante, espalhe-a.", "pronunciation": "a a-le-gree-a eh kon-ta-zhee-an-te, es-pa-lye-a."},
            {"english": "Dance like nobody's watching.", "portuguese": "Dance como se ninguém estivesse olhando.", "pronunciation": "dan-se ko-mo se neen-gem es-tee-ve-se o-lyan-do."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "portuguese": "Encontre equilíbrio na sua vida.", "pronunciation": "en-con-tre e-kwee-lee-bree-o na su-a vee-da."},
            {"english": "Work hard, rest well.", "portuguese": "Trabalhe duro, descanse bem.", "pronunciation": "tra-ba-lye du-ro, des-kan-se bem."},
            {"english": "Too much of anything is not good.", "portuguese": "O excesso de qualquer coisa não é bom.", "pronunciation": "o e-se-so de kwal-ker koy-za nao eh bom."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "portuguese": "O crescimento acontece fora da sua zona de conforto.", "pronunciation": "o cres-cee-men-to a-con-te-ce fo-ra da su-a zo-na de con-for-to."},
            {"english": "Embrace change, grow stronger.", "portuguese": "Abrace a mudança, cresça mais forte.", "pronunciation": "a-bra-se a mu-dan-sa, cres-sa meys for-te."},
            {"english": "Every challenge is a chance to grow.", "portuguese": "Cada desafio é uma chance de crescer.", "pronunciation": "ca-da de-za-fee-o eh oo-ma shan-ce de cres-ser."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "portuguese": "Encontre seu propósito, siga-o.", "pronunciation": "en-con-tre sew pro-po-zi-to, see-ga-o."},
            {"english": "Your life has meaning.", "portuguese": "Sua vida tem significado.", "pronunciation": "su-a vee-da tem sig-nee-fee-ca-do."},
            {"english": "Live with intention, not accident.", "portuguese": "Viva com intenção, não por acaso.", "pronunciation": "vee-va com in-ten-sao, nao por a-ca-zo."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "portuguese": "Esteja presente neste momento.", "pronunciation": "es-te-ja pre-sen-te nes-te mo-men-to."},
            {"english": "Breathe deeply, stay grounded.", "portuguese": "Respire fundo, mantenha-se firme.", "pronunciation": "res-pee-re fun-do, man-ten-ya se feer-me."},
            {"english": "Notice the little things around you.", "portuguese": "Observe as pequenas coisas ao seu redor.", "pronunciation": "ob-ser-ve as pe-ke-nas koy-zas ao sew re-dor."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["portuguese"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    portuguese = phrase_data.get("portuguese", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(portuguese, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Portuguese Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY PORTUGUESE"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_portuguese: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER PORTUGUESE", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_portuguese, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 FRASES ESSENCIAIS"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY PORTUGUESE", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_portuguese: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Portuguese in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_portuguese})",
        f"60 Portuguese Phrases for {category_english} | Speak Portuguese Like a Native! ({category_portuguese})",
        f"Master Portuguese {category_english} | 60 Essential Portuguese Phrases with Pronunciation | Velocity Portuguese",
        f"Portuguese Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Portuguese Fluently | {category_english} Phrases | English + Portuguese + Pronunciation",
    ]

    description = f"""🇵🇹 Learn Portuguese with Velocity Portuguese! 🇵🇹

In this video, you'll learn 60 essential Portuguese phrases about {category_english} ({category_portuguese}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Portuguese
• Correct pronunciation guide
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
📝 ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Portuguese: {phrase['portuguese']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += """
🎯 PERFECT FOR:
• Portuguese beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Portuguese language and culture
• Language enthusiasts and polyglots
• Students preparing for exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Portuguese learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY PORTUGUESE:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Portuguese Motivation Phrases
• Portuguese Love Expressions
• Basic Portuguese Greetings

#LearnPortuguese #PortuguesePhrases #PortugueseLanguage #{category_english.replace(' ', '')} #VelocityPortuguese #PortugueseForBeginners #SpeakPortuguese #PortugueseVocabulary #Pronunciation #LanguageLearning #Portuguese101 #PortugueseLesson

---
© Velocity Portuguese - Making Portuguese learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Portuguese",
            "Portuguese Phrases",
            "Portuguese Language",
            category_english,
            "Velocity Portuguese",
            "Portuguese for Beginners",
            "Speak Portuguese",
            "Portuguese Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Portuguese 101",
            "Portuguese Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_portuguese": category_portuguese,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_PORTUGUESE[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['portuguese']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Generating thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    try:
        from generate_thumbnail import generate_scenic_image
        result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
        if result and Path(result).exists():
            print(f"  gpt-image-2 thumbnail saved")
        else:
            print(f"  gpt-image-2 failed, using built-in")
            generate_thumbnail(category_english, CATEGORIES_PORTUGUESE[category_english], str(thumbnail_path))
    except Exception as e:
        print(f"  Thumbnail error: {e}, using built-in")
        generate_thumbnail(category_english, CATEGORIES_PORTUGUESE[category_english], str(thumbnail_path))

    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"

    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_PORTUGUESE[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Portuguese: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Portuguese", "Portuguese Phrases", "Portuguese", category_english, "Velocity Portuguese"],
        "category_english": category_english,
        "category_portuguese": CATEGORIES_PORTUGUESE[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Portuguese")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Portuguese YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY PORTUGUESE - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_PORTUGUESE[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
