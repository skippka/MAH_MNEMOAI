"""
Утиліти для обробки тексту та підготовки даних
"""

import re
import string
from collections import Counter
from typing import List, Dict, Any
import nltk
from nltk.corpus import stopwords
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

class TextProcessor:
    def __init__(self):
        """Ініціалізація обробника тексту"""
        # Стоп-слова для української мови
        self.ukrainian_stopwords = set([
            'і', 'в', 'у', 'з', 'на', 'не', 'що', 'та', 'до', 'за', 'для',
            'як', 'з', 'а', 'бо', 'чи', 'же', 'от', 'ні', 'так', 'але',
            'це', 'той', 'який', 'його', 'її', 'їх', 'ми', 'ви', 'вони',
            'свою', 'свої', 'своїх', 'бути', 'мати', 'робити', 'казати',
            'знати', 'мати', 'бути', 'можна', 'треба', 'повинен'
        ])
        
        # Словник для покращення якості ключових слів
        self.word_scores = {
            'сущ': 3.0,  # іменник
            'прил': 2.5,  # прикметник
            'гл': 2.0,   # дієслово
            'нар': 1.5,  # прислівник
            'спол': 1.0, # сполучник
        }
    
    def process(self, text: str) -> Dict[str, Any]:
        """Основний метод обробки тексту"""
        # Очищаємо текст
        cleaned_text = self._clean_text(text)
        
        # Токенізація
        sentences = sent_tokenize(cleaned_text, language='ukrainian')
        words = word_tokenize(cleaned_text.lower(), language='ukrainian')
        
        # Видаляємо стоп-слова
        filtered_words = [
            word for word in words 
            if word not in self.ukrainian_stopwords 
            and len(word) > 2
            and word.isalpha()
        ]
        
        # Знаходимо ключові слова
        key_words = self._extract_keywords(filtered_words)
        
        # Знаходимо ключові фрази
        key_phrases = self._extract_key_phrases(sentences)
        
        # Визначаємо основні теми
        main_topics = self._identify_topics(sentences, key_words)
        
        # Аналіз складності
        complexity = self._analyze_complexity(cleaned_text)
        
        return {
            'cleaned_text': cleaned_text,
            'sentences_count': len(sentences),
            'words_count': len(filtered_words),
            'key_words': key_words,
            'key_phrases': key_phrases,
            'main_topics': main_topics,
            'complexity': complexity,
            'readability': self._calculate_readability(cleaned_text)
        }
    
    def _clean_text(self, text: str) -> str:
        """Очищення тексту"""
        # Видаляємо спеціальні символи, але зберігаємо українські літери
        text = re.sub(r'[^\w\sА-Яа-яЄєІіЇїҐґ.,!?-]', ' ', text)
        
        # Замінюємо кілька пробілів на один
        text = re.sub(r'\s+', ' ', text)
        
        # Видаляємо цифри в середині слів
        text = re.sub(r'\b\w*\d\w*\b', '', text)
        
        return text.strip()
    
    def _extract_keywords(self, words: List[str]) -> List[Dict]:
        """Виділення ключових слів"""
        # Підрахунок частоти
        word_freq = Counter(words)
        
        # Обчислюємо TF (Term Frequency)
        total_words = len(words)
        keywords = []
        
        for word, count in word_freq.most_common(20):
            if count > 1:  # Слова, що зустрічаються більше одного разу
                tf = count / total_words
                
                # Простий спосіб визначення частини мови
                pos = self._guess_pos(word)
                score = tf * self.word_scores.get(pos, 1.0)
                
                keywords.append({
                    'word': word,
                    'frequency': count,
                    'tf': round(tf, 4),
                    'pos': pos,
                    'score': round(score, 4)
                })
        
        # Сортуємо за score
        keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return keywords[:15]  # Повертаємо топ-15
    
    def _guess_pos(self, word: str) -> str:
        """Спрощене визначення частини мови"""
        # Українські закінчення
        noun_endings = ['ня', 'сть', 'ість', 'іння', 'ення', 'ання', 'ття']
        adj_endings = ['ий', 'а', 'е', 'і', 'я', 'е', 'ова', 'ева']
        verb_endings = ['ти', 'ть', 'ла', 'ло', 'ли', 'но', 'но']
        
        if any(word.endswith(ending) for ending in noun_endings):
            return 'сущ'
        elif any(word.endswith(ending) for ending in adj_endings):
            return 'прил'
        elif any(word.endswith(ending) for ending in verb_endings):
            return 'гл'
        else:
            return 'нар'
    
    def _extract_key_phrases(self, sentences: List[str]) -> List[str]:
        """Виділення ключових фраз"""
        phrases = []
        
        for sentence in sentences:
            # Знаходимо фрази з 2-4 слів
            words = word_tokenize(sentence.lower(), language='ukrainian')
            words = [w for w in words if w.isalpha() and len(w) > 2]
            
            # Генеруємо n-грами
            for n in range(2, 5):
                for i in range(len(words) - n + 1):
                    phrase = ' '.join(words[i:i+n])
                    if len(phrase.split()) == n:
                        phrases.append(phrase)
        
        # Рахуємо частоти фраз
        phrase_freq = Counter(phrases)
        
        # Повертаємо найпопулярніші фрази
        return [phrase for phrase, count in phrase_freq.most_common(10) if count > 1]
    
    def _identify_topics(self, sentences: List[str], keywords: List[Dict]) -> List[str]:
        """Визначення основних тем"""
        topics = []
        
        # Беремо топ-5 ключових слів
        top_keywords = [kw['word'] for kw in keywords[:5]]
        
        # Шукаємо речення, де зустрічаються ключові слова
        for keyword in top_keywords:
            for sentence in sentences:
                if keyword in sentence.lower():
                    # Знаходимо найближчі слова до ключового слова
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if keyword in word.lower():
                            # Формуємо тему з контексту
                            start = max(0, i - 2)
                            end = min(len(words), i + 3)
                            topic = ' '.join(words[start:end])
                            topics.append(topic)
                            break
                    break
        
        return list(set(topics))[:5]  # Унікальні теми
    
    def _analyze_complexity(self, text: str) -> Dict[str, Any]:
        """Аналіз складності тексту"""
        sentences = sent_tokenize(text, language='ukrainian')
        words = word_tokenize(text.lower(), language='ukrainian')
        
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        
        # Розрахунок індексу читабельності
        readability = self._calculate_readability(text)
        
        return {
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_word_length': round(avg_word_length, 2),
            'readability_score': readability,
            'level': self._get_readability_level(readability)
        }
    
    def _calculate_readability(self, text: str) -> float:
        """Розрахунок читабельності (спрощена формула)"""
        sentences = sent_tokenize(text, language='ukrainian')
        words = word_tokenize(text, language='ukrainian')
        
        if not sentences or not words:
            return 0
        
        # Спрощена формула для української
        avg_sentence_len = len(words) / len(sentences)
        complex_words = [w for w in words if len(w) > 6]
        
        readability = 200 - avg_sentence_len - (len(complex_words) / len(words) * 100)
        
        return max(0, min(100, readability))
    
    def _get_readability_level(self, score: float) -> str:
        """Визначення рівня читабельності"""
        if score >= 80:
            return "Дуже легко"
        elif score >= 60:
            return "Легко"
        elif score >= 40:
            return "Помірно"
        elif score >= 20:
            return "Складно"
        else:
            return "Дуже складно"