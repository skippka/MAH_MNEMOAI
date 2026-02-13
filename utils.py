"""
Утиліти для обробки тексту та підготовки даних
"""

import re
import string
from collections import Counter
from typing import List, Dict, Any

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
        
        # Токенізація без NLTK
        sentences = self._split_sentences(cleaned_text)
        words = self._tokenize_words(cleaned_text.lower())
        
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
    
    def _split_sentences(self, text: str) -> List[str]:
        """Розбиття тексту на речення без NLTK"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]
    
    def _tokenize_words(self, text: str) -> List[str]:
        """Токенізація слів без NLTK"""
        words = re.findall(r'\b\w+\b', text)
        return words
    
    def _clean_text(self, text: str) -> str:

        text = re.sub(r'[^\w\sА-Яа-яЄєІіЇїҐґ.,!?-]', ' ', text)
        
        text = re.sub(r'\s+', ' ', text)
        
        text = re.sub(r'\b\w*\d\w*\b', '', text)
        
        return text.strip()
    
    def _extract_keywords(self, words: List[str]) -> List[Dict]:
        """Виділення ключових слів"""
        word_freq = Counter(words)
        
        total_words = len(words)
        keywords = []
        
        for word, count in word_freq.most_common(20):
            if count > 1:
                tf = count / total_words
                
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
        phrases: List[str] = []
        
        for sentence in sentences:
            # Беремо тільки буквенні, змістовні слова
            words = self._tokenize_words(sentence.lower())
            words = [w for w in words if w.isalpha() and len(w) > 2]
            
            # Формуємо фрази довжиною 2‑4 слова (класичні «ключові словосполучення»)
            for n in range(2, 5):
                for i in range(len(words) - n + 1):
                    phrase_words = words[i:i+n]
                    phrase = ' '.join(phrase_words)
                    phrases.append(phrase)
        
        if not phrases:
            return []
        
        phrase_freq = Counter(phrases)
        
        # Раніше брали тільки фрази, які зустрічаються >1 раз, тому для багатьох текстів
        # список ключових фраз був порожній. Тепер беремо і одноразові, але
        # віддаємо перевагу більш довгим та частим фразам.
        ranked = sorted(
            phrase_freq.items(),
            key=lambda item: (item[1], len(item[0].split())),
            reverse=True,
        )
        
        unique_phrases: List[str] = []
        seen = set()
        for phrase, _ in ranked:
            # Уникаємо майже однакових фраз (наприклад, з зайвим словом на кінці)
            base = phrase
            if base in seen:
                continue
            seen.add(base)
            unique_phrases.append(phrase)
            if len(unique_phrases) >= 15:
                break
        
        return unique_phrases
    
    def _identify_topics(self, sentences: List[str], keywords: List[Dict]) -> List[str]:

        topics = []
        
        top_keywords = [kw['word'] for kw in keywords[:5]]
        
        for keyword in top_keywords:
            for sentence in sentences:
                if keyword in sentence.lower():
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if keyword in word.lower():
                            start = max(0, i - 2)
                            end = min(len(words), i + 3)
                            topic = ' '.join(words[start:end])
                            topics.append(topic)
                            break
                    break
        
        return list(set(topics))[:5] 
    def _analyze_complexity(self, text: str) -> Dict[str, Any]:
        """Аналіз складності тексту"""
        sentences = self._split_sentences(text)
        words = self._tokenize_words(text.lower())
        
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
        sentences = self._split_sentences(text)
        words = self._tokenize_words(text)
        
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
