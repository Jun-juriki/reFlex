import os
import random
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()


class AIService:
    """ИИ-сервис для генерации целей и советов через GigaChat"""

    def __init__(self):
        self.client = None
        self.use_gigachat = False

        credentials = os.getenv('GIGACHAT_CREDENTIALS')
        if credentials:
            try:
                self.client = GigaChat(
                    credentials=credentials,
                    scope=os.getenv('GIGACHAT_SCOPE', 'GIGACHAT_API_PERS'),
                    verify_ssl_certs=False,
                    timeout=60.0
                )
                self.use_gigachat = True
                print("✅ GigaChat успешно инициализирован")
            except Exception as e:
                print(f"⚠️ Ошибка инициализации GigaChat: {e}")
        else:
            print("⚠️ GIGACHAT_CREDENTIALS не найден, использую fallback")

    def generate_smart_goal(self, profile):
        """Генерация SMART-цели"""
        if self.use_gigachat and self.client:
            return self._generate_via_gigachat(profile)
        return self._generate_fallback(profile)

    def _generate_via_gigachat(self, profile):
        """Генерация через GigaChat API"""
        prompt = f"""Ты — медицинский ассистент по реабилитации. Сформулируй SMART-цель для пациента.

Данные пациента:
- Диагноз: {profile.diagnosis or 'не указан'}
- Основное ограничение: {profile.limitation_type or 'двигательная функция'}
- Текущий показатель: {profile.baseline_value or 0} {profile.baseline_unit or 'ед.'}
- Срок достижения: {profile.target_days or 28} дней

Требования к цели:
- Конкретная (что именно улучшаем)
- Измеримая (с цифрами)
- Достижимая (реалистичная)
- Релевантная (связана с диагнозом)
- Ограниченная по времени

Напиши ТОЛЬКО текст цели (1-2 предложения), без пояснений.
Пример: "Увеличить дистанцию ходьбы без опоры с 50 до 150 метров за 28 дней, выполняя ежедневные упражнения."

ИСТОЧНИКИ:
1. Cochrane Library (систематические обзоры)
2. PubMed Central (рецензируемые статьи)
3. Клинические рекомендации Минздрава РФ
4. ВОЗ: Всемирная организация здравоохранения
Не вставляй ссылки на источники. Можешь просто ссылаться на название организации или лицензированной методички.
ПРАВИЛА:
- Каждое утверждение должно быть из этих источников
- Если информации нет - скажи "Нет данных"
- Не используй общие знания или предположения

Задание: составь программу реабилитации для пациента с {profile.diagnosis}.
"""
        try:
            print("📤 Отправка запроса к GigaChat...")
            response = self.client.chat(prompt)
            goal_text = response.choices[0].message.content.strip()
            print(f"✅ Получен ответ: {goal_text[:50]}...")
            return goal_text
        except Exception as e:
            print(f"❌ Ошибка GigaChat: {e}")
            return self._generate_fallback(profile)

    def generate_exercise_program(self, profile):
        """Генерация полной программы тренировок с подробными описаниями"""
        """Генерация программы с подробными описаниями через GigaChat"""
        
        prompt = f"""Ты — профессиональный реабилитолог. Составь ПОДРОБНУЮ программу тренировок. 

    ДАННЫЕ ПАЦИЕНТА:
    - Диагноз: {profile.diagnosis or 'не указан'}
    - Основное ограничение: {profile.limitation_type or 'двигательная функция'}
    - Текущий показатель: {profile.baseline_value or 0} {profile.baseline_unit or 'ед.'}
    - Срок восстановления: {profile.target_days or 28} дней

    ТРЕБОВАНИЯ К ПРОГРАММЕ:
    Создай ровно 3 упражнения: РАЗМИНКА, ОСНОВНОЕ, ЗАКРЕПЛЕНИЕ.

    Для КАЖДОГО упражнения дай ПОДРОБНОЕ описание (минимум 3-4 предложения):
    1. Исходное положение
    2. Техника выполнения (пошагово)
    3. На что обратить внимание
    4. Какие мышцы работают
    5. Ошибки, которых нужно избегать

    Уровни прогрессии:
    - level_1: первые 10 дней
    - level_2: дни 11-20
    - level_3: дни 21-28

    Верни ТОЛЬКО JSON, полностью его заполни. Пример:
    [
        {{
            "name": "Разминка плечевого пояса",
            "description": "Исходное положение: сидя на стуле, спина прямая, ноги на ширине плеч. Шаг 1: медленно поднимите плечи вверх на вдохе, опустите на выдохе. Повторите 5-7 раз. Шаг 2: делайте круговые движения плечами вперёд и назад. Важно: не напрягайте шею, дышите ровно. Это упражнение улучшает кровообращение в плечевом суставе. Ошибки: резкие движения, задержка дыхания, поднятие плеч к ушам.",
            "progression": {{
                "level_1": "5-7 минут, 2 подхода",
                "level_2": "7-10 минут, 3 подхода",
                "level_3": "10-12 минут, 4 подхода",
                "upgrade_every": "7 дней"
            }}
        }}
    ]

    ИСТОЧНИКИ: Клинические рекомендации Минздрава РФ, ВОЗ.
    ОПИСАНИЯ ДОЛЖНЫ БЫТЬ МАКСИМАЛЬНО ПОДРОБНЫМИ и ПОЛЕЗНЫМИ для пациента."""
        
        try:
            print("📤 Генерация подробной программы тренировок...")
            response = self.client.chat(prompt)
            text = response.choices[0].message.content
            print(f"📝 Получен ответ (длина: {len(text)} символов)")
            
            # Ищем JSON в ответе
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end != 0:
                import json
                json_str = text[start:end]
                program = json.loads(json_str)
                print(f"✅ Программа сгенерирована: {len(program)} упражнений")
                return program
            else:
                print("⚠️ JSON не найден, использую fallback")
                return self._generate_program_fallback(profile)
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return self._generate_program_fallback(profile)
        
    def generate_advice(self, progress_percent, days_diff, streak, level):
        """Генерация мотивационного совета"""
        if self.use_gigachat and self.client:
            return self._generate_advice_via_gigachat(progress_percent, days_diff, streak, level)
        return self._generate_advice_fallback()

    def _generate_advice_via_gigachat(self, progress_percent, days_diff, streak, level):
        """Генерация совета через GigaChat"""
        # Определяем тон
        if progress_percent >= 80:
            tone = "восторженный и поздравляющий"
        elif progress_percent >= 50:
            tone = "ободряющий"
        elif progress_percent >= 20:
            tone = "мотивирующий"
        else:
            tone = "мягкий и поддерживающий"

        ahead_text = "опережает" if days_diff < 0 else "отстает от"
        abs_diff = abs(days_diff)

        prompt = f"""Ты — дружелюбный AI-тренер в приложении для реабилитации. Напиши короткий совет пациенту.

    Статистика:
    - Прогресс: {progress_percent:.0f}% от цели
    - Пациент {ahead_text} графика на {abs_diff:.0f} дней
    - Серия: {streak} дней подряд
    - Уровень: {level}

    Твой тон: {tone}

    Требования:
    - Максимум 2 предложения
    - Без медицинских терминов
    - Позитивно и поддерживающе

    Примеры:
    "🔥 Отличный прогресс! Не забывай делать разминку перед тренировкой."
    "💪 Ты почти у цели! Добавь вечернюю прогулку для ускорения."
    """
        try:
            response = self.client.chat(prompt)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Ошибка генерации совета: {e}")
            return self._generate_advice_fallback()

    def _generate_advice_fallback(self):
        """Запасные фразы для советов"""
        advices = [
            "🔥 Отличная работа! Продолжай в том же духе!",
            "💪 Каждый день приближает к цели! Так держать!",
            "⭐ Ты делаешь успехи! Не останавливайся!",
            "🎯 Сегодня отличный день для тренировки!",
            "🌟 Твой прогресс впечатляет! Продолжай в том же темпе!"
        ]
        return random.choice(advices)


# Глобальный экземпляр сервиса
ai_service = AIService()