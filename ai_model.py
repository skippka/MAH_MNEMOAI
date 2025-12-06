"""
Спрощена модель ШІ для генерації мнемонік з використанням легких моделей
"""

import random
import re
from typing import List, Dict, Any
import json
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

# Завантажуємо ресурси NLTK
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class MnemonicGenerator:
    def __init__(self):
        print("Ініціалізація MnemonicGenerator...")
        
        self.mnemonic_techniques = {
            'acronym': {
                'name': 'Акроніми',
                'description': 'Створення слова з перших літер ключових понять'
            },
            'acrostic': {
                'name': 'Акростихи',
                'description': 'Вірш, де перші літери кожного рядка утворюють слово'
            },
            'rhyme': {
                'name': 'Рими',
                'description': 'Римовані правила для запам\'ятовування'
            },
            'story': {
                'name': 'Асоціативні історії',
                'description': 'Створення яскравих історій з ключовими поняттями'
            },
            'loci': {
                'name': 'Метод локуса',
                'description': 'Прив\'язка інформації до знайомих місць'
            },
            'number': {
                'name': 'Число-образ',
                'description': 'Асоціація чисел з яскравими образами'
            }
        }
        
        self.word_base = self._load_word_base()
        self.rhyme_patterns = self._load_rhyme_patterns()
        self.story_templates = self._load_story_templates()
        
        print("Мнемонічний генератор успішно ініціалізовано!")
    
    def _load_word_base(self):
        """Завантаження бази слів для генерації"""
        # База українських слів для мнемонік
        return {
            'nouns': [
                'сонце', 'місяць', 'зірка', 'хмара', 'дощ', 'вітер', 'гора',
                'ріка', 'ліс', 'поле', 'квітка', 'дерево', 'будинок', 'кімната',
                'стіл', 'стілець', 'книга', 'олівець', 'папір', 'світло'
            ],
            'verbs': [
                'біжить', 'летить', 'пливе', 'стоїть', 'лежить', 'спить',
                'говорить', 'чує', 'бачить', 'знає', 'розуміє', 'вчить',
                'пам\'ятає', 'згадує', 'думає', 'уявляє', 'створює', 'будує'
            ],
            'adjectives': [
                'великий', 'маленький', 'яскравий', 'темний', 'швидкий',
                'повільний', 'мудрий', 'цікавий', 'важливий', 'основний',
                'головний', 'перший', 'останній', 'середній', 'спеціальний'
            ],
            'acronym_words': [
                'СОНЦЕ', 'ВІТЕР', 'ГРАФІК', 'МОДУЛЬ', 'СИСТЕМА', 'ФОРМУЛА',
                'ТЕМП', 'РИТМ', 'КОД', 'ЗНАК', 'СИМВОЛ', 'ОБРАЗ', 'ПЛАН'
            ]
        }
    
    def _load_rhyme_patterns(self):
        """Завантаження шаблонів рим"""
        return [
            "Щоб запам'ятати {word}, треба знати {rhyme}",
            "{word} - це важливо, {rhyme}",
            "Для {word} є правило: {rhyme}",
            "{word} запам'ятовується так: {rhyme}"
        ]
    
    def _load_story_templates(self):
        """Завантаження шаблонів історій"""
        return [
            "Уявіть собі, що {items}. Це допоможе запам'ятати ключові поняття.",
            "Одного разу {items}. Ця історія символізує основні ідеї.",
            "Представте собі світ, де {items}. Така асоціація полегшить запам'ятовування."
        ]
    
    def generate_mnemonics(self, key_phrases: List[str], main_topics: List[str]) -> Dict[str, Any]:
        """Генерація мнемонік на основі ключових фраз"""
        mnemonics = {}
        
        # 1. Акроніми
        mnemonics['acronyms'] = self._generate_acronyms(key_phrases)
        
        # 2. Акростихи
        mnemonics['acrostics'] = self._generate_acrostics(main_topics)
        
        # 3. Рифи
        mnemonics['rhymes'] = self._generate_rhymes(key_phrases)
        
        # 4. Історії
        mnemonics['stories'] = self._generate_stories(key_phrases)
        
        # 5. Метод локуса
        mnemonics['loci_method'] = self._generate_loci_method(key_phrases)
        
        # 6. Візуальні асоціації
        mnemonics['visuals'] = self._generate_visual_associations(key_phrases)
        
        # 7. Числові асоціації
        mnemonics['number_associations'] = self._generate_number_associations(key_phrases)
        
        return mnemonics
    
    def _generate_acronyms(self, key_phrases: List[str]) -> List[Dict]:
        """Генерація акронімів"""
        results = []
        
        if not key_phrases:
            return results
        
        # Беремо до 7 ключових фраз для акроніма
        phrases = key_phrases[:7]
        
        # Отримуємо перші літери
        letters = []
        for phrase in phrases:
            if phrase and len(phrase.strip()) > 0:
                # Беремо першу літеру, перетворюємо на велику
                first_letter = phrase.strip()[0].upper()
                # Замінюємо українські літери на латинські аналоги для акроніму
                ukr_to_lat = {
                    'І': 'I', 'Ї': 'YI', 'Є': 'YE', 'Ґ': 'G',
                    'і': 'I', 'ї': 'YI', 'є': 'YE', 'ґ': 'G'
                }
                letters.append(ukr_to_lat.get(first_letter, first_letter))
        
        if len(letters) >= 3:
            # Складаємо слово з літер
            acronym = ''.join(letters)
            
            # Генеруємо кілька варіантів
            for i in range(min(3, len(self.word_base['acronym_words']))):
                suggested_word = self.word_base['acronym_words'][i]
                
                results.append({
                    'word': suggested_word,
                    'acronym': acronym,
                    'letters': letters,
                    'mapping': [
                        {'letter': letters[j], 'phrase': phrases[j]}
                        for j in range(len(letters))
                    ],
                    'explanation': f'Використовуйте слово "{suggested_word}" для запам\'ятовування послідовності'
                })
        
        # Якщо не вдалося створити, використовуємо простий варіант
        if not results and letters:
            simple_acronym = ''.join(letters)
            results.append({
                'word': simple_acronym,
                'acronym': simple_acronym,
                'letters': letters,
                'mapping': [
                    {'letter': letters[i], 'phrase': phrases[i]}
                    for i in range(len(letters))
                ],
                'explanation': 'Використовуйте цей акронім як мнемонічний код'
            })
        
        return results
    
    def _generate_acrostics(self, topics: List[str]) -> List[Dict]:
        """Генерація акростихів"""
        results = []
        
        if not topics:
            return results
        
        topic = topics[0]
        # Беремо перші літери з теми для створення акростиха
        topic_letters = [letter.upper() for letter in topic if letter.isalpha()]
        
        if len(topic_letters) >= 3:
            acrostic_word = ''.join(topic_letters[:5])
            
            # Створюємо простий акростих
            lines = []
            words_for_lines = self.word_base['nouns'][:len(topic_letters)]
            
            for i, letter in enumerate(topic_letters[:5]):
                if i < len(words_for_lines):
                    line = f"{letter} - {words_for_lines[i].capitalize()} і яскраво сяє"
                    lines.append(line)
            
            acrostic = '\n'.join(lines)
            
            results.append({
                'topic': topic,
                'acrostic': acrostic,
                'word': acrostic_word,
                'lines': len(lines),
                'explanation': f'Кожен рядок починається з літери слова "{acrostic_word}"'
            })
        
        return results
    
    def _generate_rhymes(self, phrases: List[str]) -> List[Dict]:
        """Генерація римованих правил"""
        results = []
        
        if not phrases:
            return results
        
        # Беремо 3-5 фраз для рими
        selected_phrases = phrases[:min(5, len(phrases))]
        
        rhyme_words = []
        for phrase in selected_phrases:
            # Беремо ключове слово з фрази
            words = phrase.split()
            if words:
                # Беремо останнє слово як основу для рими
                base_word = words[-1].lower().strip('.,!?')
                rhyme_words.append(base_word)
        
        if rhyme_words:
            # Створюємо римоване правило
            template = random.choice(self.rhyme_patterns)
            
            # Знаходимо римуючі слова
            rhyme_pairs = []
            for word in rhyme_words[:3]:
                # Проста рима - додаємо закінчення
                if word.endswith(('а', 'я')):
                    rhyme = word[:-1] + 'ий'
                elif word.endswith(('о', 'е')):
                    rhyme = word[:-1] + 'ий'
                else:
                    rhyme = word + 'ий'
                rhyme_pairs.append((word, rhyme))
            
            # Створюємо римований текст
            rhyme_text = ", ".join([f"{w} римує з {r}" for w, r in rhyme_pairs])
            
            results.append({
                'phrases': selected_phrases,
                'rhyme': template.format(word=selected_phrases[0], rhyme=rhyme_text),
                'type': 'Римоване правило',
                'explanation': 'Використовуйте ритм для кращого запам\'ятовування'
            })
        
        return results
    
    def _generate_stories(self, phrases: List[str]) -> List[Dict]:
        """Генерація асоціативних історій"""
        results = []
        
        if not phrases:
            return results
        
        # Обмежуємо кількість фраз для історії
        story_phrases = phrases[:min(6, len(phrases))]
        
        # Створюємо список елементів для історії
        items_list = []
        for i, phrase in enumerate(story_phrases):
            # Спрощуємо фрази для історії
            simple_phrase = phrase.split()[0] if phrase.split() else phrase
            items_list.append(f"{simple_phrase} {random.choice(self.word_base['verbs'])}")
        
        if items_list:
            # Вибираємо шаблон
            template = random.choice(self.story_templates)
            items_text = ", потім ".join(items_list)
            
            story = template.format(items=items_text)
            
            results.append({
                'phrases': story_phrases,
                'story': story,
                'length': len(story),
                'explanation': 'Уявіть цю історію візуально для кращого запам\'ятовування'
            })
        
        return results
    
    def _generate_loci_method(self, phrases: List[str]) -> List[Dict]:
        """Генерація методом локуса"""
        locations = [
            "вхідні двері", "вікно в вітальні", "обідній стіл", "комп'ютерний стіл",
            "книжкова шафа", "кухонна плита", "ванна кімната", "балкон",
            "спальне ліжко", "телевізор", "холодильник", "зеркало",
            "диван", "полиця з книгами", "робочий стіл", "підвіконня"
        ]
        
        results = []
        
        # Зв'язуємо фрази з місцями
        for i, phrase in enumerate(phrases[:10]):
            if i < len(locations):
                # Спрощуємо фразу
                simple_phrase = phrase.split()[0] if phrase.split() else phrase[:20]
                
                results.append({
                    'phrase': simple_phrase,
                    'location': locations[i],
                    'association': f"Уявіть '{simple_phrase}' біля {locations[i]}",
                    'visualization': f"Прокоментуйте: Як виглядає {simple_phrase} на {locations[i]}?"
                })
        
        return results
    
    def _generate_visual_associations(self, phrases: List[str]) -> List[Dict]:
        """Генерація візуальних асоціацій"""
        visual_templates = [
            "Уявіть {phrase} у вигляді {image}",
            "{phrase} нагадує {association}",
            "Порівняйте {phrase} з {comparison}",
            "Зобразіть {phrase} як {visual}"
        ]
        
        common_images = [
            "яскравого сонця", "великої гори", "швидкої річки",
            "квітучого дерева", "мудрої сови", "сильного ведмедя",
            "швидкого поїзда", "високого будинку", "глибокого моря",
            "яскравої зірки", "теплого вогню", "свіжого вітру"
        ]
        
        colors = [
            "червоного", "синього", "зеленого", "жовтого", "фіолетового",
            "помаранчевого", "рожевого", "білого", "чорного", "золотого"
        ]
        
        results = []
        
        for i, phrase in enumerate(phrases[:8]):
            template = random.choice(visual_templates)
            image = random.choice(common_images)
            color = random.choice(colors)
            
            # Спрощуємо фразу
            simple_phrase = phrase.split()[0] if phrase.split() else phrase[:15]
            
            visualization = template.format(
                phrase=simple_phrase,
                image=f"{color} {image}",
                association=f"{color} {image}",
                comparison=f"{color} {image}",
                visual=f"{color} {image}"
            )
            
            results.append({
                'phrase': simple_phrase,
                'visualization': visualization,
                'suggested_image': f"{color} {image}",
                'explanation': 'Створіть яскравий ментальний образ'
            })
        
        return results
    
    def _generate_number_associations(self, phrases: List[str]) -> List[Dict]:
        """Генерація числових асоціацій"""
        number_images = {
            1: "стовп", 2: "лебідь", 3: "тризуб", 4: "човен", 5: "гачок",
            6: "вишня", 7: "коса", 8: "очки", 9: "куля", 10: "пальці",
            11: "близнюки", 12: "годинник", 13: "чорт", 14: "кілт", 15: "пенал",
            20: "гуска", 30: "трійка", 40: "сорок", 50: "полтинник", 100: "сотня"
        }
        
        results = []
        
        for i, phrase in enumerate(phrases[:10]):
            num = i + 1
            if num in number_images:
                simple_phrase = phrase.split()[0] if phrase.split() else phrase[:15]
                
                results.append({
                    'number': num,
                    'phrase': simple_phrase,
                    'image': number_images[num],
                    'association': f"{num} = {number_images[num]} → асоціюйте з '{simple_phrase}'",
                    'explanation': f'Зв\'яжіть число {num} з образом "{number_images[num]}" для запам\'ятовування'
                })
        
        return results
    
    def generate_story(self, keywords: List[str]) -> str:
        """Генерація історії на основі ключових слів"""
        if not keywords:
            return "Будь ласка, введіть ключові слова для генерації історії."
        
        story_intros = [
            "Уявіть собі неймовірну пригоду, де ",
            "Колись давно в чарівному світі ",
            "Одного разу трапилася дивовижна історія: ",
            "У світі знань та пам'яті існує таємниця: "
        ]
        
        connectors = [
            " потім ", " аж раптом ", " несподівано ", " і тоді ",
            " одночасно ", " через деякий час ", " між тим "
        ]
        
        intro = random.choice(story_intros)
        story = intro
        
        for i, keyword in enumerate(keywords):
            # Спрощуємо ключове слово
            simple_keyword = keyword.split()[0] if keyword.split() else keyword
            
            # Додаємо дію
            action = random.choice(self.word_base['verbs'])
            story += f"'{simple_keyword}' {action}"
            
            if i < len(keywords) - 1:
                story += random.choice(connectors)
            else:
                story += ". Ця історія допоможе вам запам'ятати ключові поняття."
        
        return story
    
    def generate_summary(self, processed_data: Dict) -> str:
        """Генерація резюме тексту"""
        if not processed_data or 'key_phrases' not in processed_data:
            return "Немає даних для резюме."
        
        key_phrases = processed_data.get('key_phrases', [])
        main_topics = processed_data.get('main_topics', [])
        
        if not key_phrases and not main_topics:
            return "Текст занадто короткий для резюме."
        
        # Створюємо просте резюме
        summary_parts = []
        
        if main_topics:
            summary_parts.append(f"Основні теми: {', '.join(main_topics[:3])}.")
        
        if key_phrases:
            summary_parts.append(f"Ключові поняття: {', '.join(key_phrases[:5])}.")
        
        summary_parts.append("Використовуйте згенеровані мнемоніки для ефективного запам'ятовування.")
        
        return " ".join(summary_parts)
    
    def generate_quiz(self, text: str) -> List[Dict]:
        """Генерація тесту на основі тексту"""
        questions = []
        
        if not text or len(text) < 50:
            return questions
        
        # Простий алгоритм для генерації питань
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        for i, sentence in enumerate(sentences[:5]):  # Обмежуємо 5 питаннями
            words = sentence.split()
            if len(words) > 5:
                # Вибираємо ключове слово для заміни (не перше і не останнє)
                if len(words) > 3:
                    key_index = min(3, len(words) - 2)
                    key_word = words[key_index]
                else:
                    key_word = words[0]
                
                # Створюємо питання з пропуском
                question_words = words.copy()
                question_words[key_index] = "_____"
                question_text = ' '.join(question_words) + '.'
                
                # Генеруємо варіанти відповідей
                options = [key_word]
                
                # Додаємо інші слова з речення (крім стоп-слів)
                other_words = [w for w in words if w != key_word and len(w) > 3]
                random.shuffle(other_words)
                
                # Додаємо 3 неправильні варіанти
                for wrong_word in other_words[:3]:
                    if wrong_word not in options and len(options) < 4:
                        options.append(wrong_word)
                
                # Якщо не вистачило варіантів, додаємо схожі слова
                while len(options) < 4:
                    fake_word = f"слово{i+1}"
                    options.append(fake_word)
                
                random.shuffle(options)
                
                questions.append({
                    'id': i + 1,
                    'question': question_text,
                    'options': options,
                    'correct': key_word,
                    'explanation': f'Це ключове слово з оригінального тексту'
                })
        
        return questions
    
    def get_memory_tips(self) -> List[str]:
        """Поради для покращення пам'яті"""
        tips = [
            "📚 Вивчайте матеріал дрібними порціями по 25-30 хвилин",
            "🔄 Повторюйте інформацію через зростаючі інтервали (1 день, 3 дні, тиждень)",
            "🎨 Використовуйте візуалізацію та кольорові маркери для виділення ключових моментів",
            "🔗 Створюйте асоціації з уже відомою інформацією",
            "🗣️ Навчайте інших - це найкращий спосіб запам'ятати матеріал",
            "🎵 Створюйте ритмічні або мелодійні мнемоніки",
            "📍 Використовуйте метод локуса (палац пам'яті) для складних послідовностей",
            "💤 Не забувайте про здоровий сон для консолідації пам'яті",
            "🧠 Тренуйте пам'ять регулярно, як м'яз",
            "🎯 Фокусуйтеся на одному завданні за раз",
            "✍️ Конспектуйте своїми словами",
            "🕰️ Використовуйте техніку Помодоро (25 хвилин навчання, 5 хвилин відпочинку)",
            "🧩 Розбивайте складну інформацію на частини",
            "🎭 Використовуйте емоції - емоційно забарвлена інформація краще запам'ятовується",
            "🏃‍♂️ Фізична активність покращує мозкову діяльність"
        ]
        
        # Повертаємо 5 випадкових порад
        return random.sample(tips, 5) if len(tips) >= 5 else tips
    
    def analyze_text_complexity(self, text: str) -> Dict[str, Any]:
        """Аналіз складності тексту"""
        if not text:
            return {
                'level': 'Невідомий',
                'score': 0,
                'description': 'Текст відсутній'
            }
        
        # Простий аналіз довжини
        words = text.split()
        sentences = text.split('.')
        
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        
        # Визначаємо рівень складності
        if avg_sentence_length < 10:
            level = 'Дуже легко'
            score = 85
        elif avg_sentence_length < 15:
            level = 'Легко'
            score = 70
        elif avg_sentence_length < 20:
            level = 'Помірно'
            score = 50
        elif avg_sentence_length < 25:
            level = 'Складно'
            score = 30
        else:
            level = 'Дуже складно'
            score = 15
        
        return {
            'level': level,
            'score': score,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_word_length': round(avg_word_length, 1),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'description': f'Текст {level.lower()}, середня довжина речення: {avg_sentence_length:.1f} слів'
        }

# Якщо файл запускається напряму
if __name__ == "__main__":
    # Тестування генератора
    generator = MnemonicGenerator()
    
    # Тестовий текст
    test_phrases = ["Економічна функція", "Соціальна відповідальність", 
                    "Інноваційний розвиток", "Ресурсне забезпечення"]
    
    test_topics = ["Функції підприємства", "Менеджмент та управління"]
    
    print("Тестування генерації мнемонік...")
    mnemonics = generator.generate_mnemonics(test_phrases, test_topics)
    
    print("\nЗгенеровані акроніми:")
    for acronym in mnemonics.get('acronyms', []):
        print(f"  - {acronym['word']}: {acronym['explanation']}")
    
    print("\nЗгенеровані історії:")
    for story in mnemonics.get('stories', []):
        print(f"  - {story['story'][:100]}...")
    
    print("\nПоради для пам'яті:")
    for tip in generator.get_memory_tips():
        print(f"  - {tip}")