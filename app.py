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
        
        if not text or len(text.strip()) < 10:
            return jsonify({
                'success': False,
                'error': 'Текст занадто короткий. Мінімум 10 символів.'
            })
        
        # Обробляємо текст
        processed_data = text_processor.process(text)
        
        # Генеруємо мнемоніки за допомогою ШІ
        mnemonics = generator.generate_mnemonics(
            processed_data['key_phrases'],
            processed_data['main_topics']
        )
        
        # Створюємо унікальний ID для сесії
        session_id = str(uuid.uuid4())[:8]
        
        # Зберігаємо результати
        result_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'original_text': text[:500] + '...' if len(text) > 500 else text,
            'processed_data': processed_data,
            'mnemonics': mnemonics,
            'summary': generator.generate_summary(processed_data)
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
            
            # Генеруємо мнемоніки
            mnemonics = generator.generate_mnemonics(
                processed_data['key_phrases'],
                processed_data['main_topics']
            )
            
            session_id = str(uuid.uuid4())[:8]
            
            result_data = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'original_text': text[:500] + '...' if len(text) > 500 else text,
                'processed_data': processed_data,
                'mnemonics': mnemonics,
                'summary': generator.generate_summary(processed_data)
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
    try:
        filename = f"static/user_data/session_{session_id}.json"
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return render_template('result.html', data=data)
        
    except FileNotFoundError:
        return render_template('error.html', message='Сесія не знайдена')

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
