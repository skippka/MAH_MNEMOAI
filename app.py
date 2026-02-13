"""
Мнемонічний тренер з ШІ - Flask веб-додаток
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
from werkzeug.utils import secure_filename

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_model import MnemonicGenerator
from utils import TextProcessor
import json
import uuid
from datetime import datetime
from gemini_client import get_gemini_client

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'docx', 'md'}

# Створюємо папки
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/user_data', exist_ok=True)

# Ініціалізуємо модель ШІ
generator = MnemonicGenerator()

# Ініціалізуємо обробник тексту
text_processor = TextProcessor()


@app.route('/api/gemini_help', methods=['POST'])
def gemini_help():
    """API для покращення/редагування тексту за допомогою Google Gemini"""
    try:
        data = request.json or {}
        text = data.get('text', '') or ''
        language = data.get('language', 'uk')

        if not text or len(text.strip()) < 10:
            return jsonify({
                'success': False,
                'error': 'Текст занадто короткий для покращення. Мінімум 10 символів.'
            }), 400

        client = get_gemini_client()
        improved_text = client.improve_text(text, language=language)

        return jsonify({
            'success': True,
            'improved_text': improved_text
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Помилка Gemini: {str(e)}'
        }), 500

@app.route('/')
def index():
    """Головна сторінка"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Сторінка завантаження"""
    return render_template('upload.html')

@app.route('/api/process_text', methods=['POST'])
def process_text():
    """API для обробки тексту"""
    try:
        data = request.json
        text = data.get('text', '')
        mode = data.get('mode', 'normal')
        
        if not text or len(text.strip()) < 10:
            return jsonify({
                'success': False,
                'error': 'Текст занадто короткий. Мінімум 10 символів.'
            })
        
        ai_full = None
        if mode == 'deep':
            # ГЛИБОКЕ МИСЛЕННЯ: усе робить нейромережа
            try:
                client = get_gemini_client()
                ai_full = client.generate_full_mnemonics(text)
                
                # Відладочна інформація (можна видалити після тестування)
                tips_from_gemini = ai_full.get('tips', [])
                if not tips_from_gemini or len(tips_from_gemini) == 0:
                    print(f"⚠️ УВАГА: Gemini не повернула поради або повернула порожній масив. ai_full.keys() = {list(ai_full.keys())}")
                else:
                    print(f"✅ Gemini повернула {len(tips_from_gemini)} порад")
                
                # Якщо успішно отримали дані від нейромережі
                analysis = ai_full.get('analysis', {})
                processed_data = {
                    'cleaned_text': text,
                    'sentences_count': analysis.get('sentence_count', 0),
                    'words_count': analysis.get('word_count', 0),
                    'key_words': analysis.get('keywords', []),
                    'key_phrases': [],
                    'main_topics': [],
                    'complexity': {
                        'level': analysis.get('complexity_level', 'Невідомий')
                    },
                    'readability': 0,
                }

                # Усі мнемоніки – рядки від нейромережі
                mnemonics = {
                    'acronyms': ai_full.get('acronyms', []),
                    'acrostics': ai_full.get('acrostics', []),
                    'stories': ai_full.get('stories', []),
                    'rhymes': ai_full.get('rhymes', []),
                    'visuals': ai_full.get('visuals', []),
                }

                summary_text = "Глибоке мислення: повний аналіз та мнемоніки створені нейромережею."
                # Беремо поради від Gemini, якщо вони є і не пусті
                gemini_tips = ai_full.get('tips', [])
                if not gemini_tips or (isinstance(gemini_tips, list) and len(gemini_tips) == 0):
                    # Якщо Gemini не повернула поради - використовуємо порожній список
                    # (не будемо підміняти локальними, щоб було видно що Gemini не дала порад)
                    gemini_tips = []
                
                ai_memory = {
                    "study_plan": ai_full.get('study_plan', ''),
                    "tips": gemini_tips,  # Тільки поради від Gemini
                    "mnemonics": [],
                }
            except RuntimeError as e:
                # Якщо помилка квоти - fallback на локальну генерацію
                error_msg = str(e)
                if "квот" in error_msg.lower() or "quota" in error_msg.lower():
                    # Переходимо на звичайний режим
                    mode = 'normal'
                else:
                    # Інша помилка - прокидаємо далі
                    raise
            except Exception:
                # Будь-яка інша помилка - fallback на локальну генерацію
                mode = 'normal'
        
        if mode != 'deep' or ai_full is None:
            # ЗВИЧАЙНЕ МИСЛЕННЯ: локальна модель (або fallback з глибокого)
            # ЗВИЧАЙНЕ МИСЛЕННЯ: локальна модель
            processed_data = text_processor.process(text)

            mnemonics = generator.generate_mnemonics(
                processed_data['key_phrases'],
                processed_data['main_topics']
            )

            # План/поради локально
            try:
                plan = generator.create_comprehensive_plan(text, processed_data.get('key_phrases', []))
                study_lines = []
                for phase in plan.get('phases', []):
                    name = phase.get('name', 'Фаза')
                    dur = phase.get('duration', '-')
                    study_lines.append(f"{name} ({dur})")
                    for a in phase.get('actions', []):
                        study_lines.append(f" - {a}")
                ai_memory = {
                    "study_plan": "\n".join(study_lines) if study_lines else "План не вдалося згенерувати.",
                    "tips": plan.get('memory_tips', generator.get_memory_tips()),
                    "mnemonics": []
                }
            except Exception:
                ai_memory = {
                    "study_plan": "План не вдалося згенерувати.",
                    "tips": generator.get_memory_tips(),
                    "mnemonics": []
                }

            summary_text = generator.generate_summary(processed_data)
        
        # Створюємо унікальний ID для сесії
        session_id = str(uuid.uuid4())[:8]
        
        # Зберігаємо результати
        result_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'original_text': text[:500] + '...' if len(text) > 500 else text,
            'processed_data': processed_data,
            'mnemonics': mnemonics,
            'summary': summary_text if mode == 'deep' else summary_text,
            'ai_memory': ai_memory,
            'ai_full': ai_full if mode == 'deep' else None,
        }
        
        # Зберігаємо у файл
        filename = f"static/user_data/session_{session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'data': result_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/upload_file', methods=['POST'])
def upload_file():
    """API для завантаження файлу"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Немає файлу'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не вибрано'})
        
        if file:
            # Читаємо вміст файлу
            if file.filename.endswith('.txt'):
                text = file.read().decode('utf-8')
            elif file.filename.endswith('.pdf'):
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
            elif file.filename.endswith('.docx'):
                from docx import Document
                doc = Document(file)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                return jsonify({'success': False, 'error': 'Формат файлу не підтримується'})
            
            # Обробляємо текст
            processed_data = text_processor.process(text)
            
            # Генеруємо мнемоніки класичним генератором (локальний ШІ)
            mnemonics = generator.generate_mnemonics(
                processed_data['key_phrases'],
                processed_data['main_topics']
            )

            # Для завантажених файлів використовуємо лише локальний план (без Gemini),
            # щоб "глибоке мислення" було лише для тексту з форми.
            try:
                plan = generator.create_comprehensive_plan(text, processed_data.get('key_phrases', []))
                study_lines = []
                for phase in plan.get('phases', []):
                    name = phase.get('name', 'Фаза')
                    dur = phase.get('duration', '-')
                    study_lines.append(f"{name} ({dur})")
                    for a in phase.get('actions', []):
                        study_lines.append(f" - {a}")
                ai_memory = {
                    "study_plan": "\n".join(study_lines) if study_lines else "План не вдалося згенерувати.",
                    "tips": plan.get('memory_tips', generator.get_memory_tips()),
                    "mnemonics": []
                }
            except Exception:
                ai_memory = {
                    "study_plan": "План не вдалося згенерувати.",
                    "tips": generator.get_memory_tips(),
                    "mnemonics": []
                }
            
            session_id = str(uuid.uuid4())[:8]
            
            result_data = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'original_text': text[:500] + '...' if len(text) > 500 else text,
                'processed_data': processed_data,
                'mnemonics': mnemonics,
                'summary': generator.generate_summary(processed_data),
                'ai_memory': ai_memory,
            }
            
            filename = f"static/user_data/session_{session_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'data': result_data
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Помилка обробки файлу: {str(e)}'
        })

@app.route('/result/<session_id>')
def show_result(session_id):
    """Сторінка результатів"""
    return render_template('result.html')

@app.route('/api/result/<session_id>')
def api_get_result(session_id):
    """API для отримання результатів сесії"""
    try:
        filename = f"static/user_data/session_{session_id}.json"
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Сесія не знайдена'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get_memory_tips')
def get_memory_tips():
    """API для отримання порад щодо пам'яті"""
    tips = generator.get_memory_tips()
    return jsonify({'tips': tips})

@app.route('/api/generate_story', methods=['POST'])
def generate_story():
    """API для генерації історії на основі ключових слів"""
    try:
        data = request.json
        keywords = data.get('keywords', [])
        
        if not keywords:
            return jsonify({'success': False, 'error': 'Немає ключових слів'})
        
        story = generator.generate_story(keywords)
        
        return jsonify({
            'success': True,
            'story': story
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/quiz', methods=['POST'])
def generate_quiz():
    """API для генерації тесту на основі тексту"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'Немає тексту'})
        
        quiz = generator.generate_quiz(text)
        
        return jsonify({
            'success': True,
            'quiz': quiz
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
