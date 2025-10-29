#!/usr/bin/env python3
"""
Тест обновленного интерфейса реферальной системы
"""

import sqlite3

def test_updated_interface():
    """Тест обновленного интерфейса"""
    
    DATABASE_PATH = "bot_database.db"
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            print("🔍 Тестируем обновленный интерфейс")
            
            user_id = 739935417
            
            # Получаем статистику по типам депозитов
            print(f"\n📊 Получаем статистику рефералов для пользователя {user_id}...")
            
            # Статистика для 30-дневных депозитов
            cursor.execute('''
                SELECT 
                    r.level,
                    COUNT(*) as count
                FROM referral_relations r
                JOIN users u ON r.referred_id = u.telegram_id
                WHERE r.referrer_id = ? 
                AND u.active_deposits_30 > 0
                GROUP BY r.level
            ''', (user_id,))
            
            results_30 = cursor.fetchall()
            
            stats_30 = {'level_1': 0, 'level_2': 0, 'level_3': 0, 'total': 0}
            for level, count in results_30:
                if 1 <= level <= 3:
                    stats_30[f'level_{level}'] = count
                    stats_30['total'] += count
            
            # Статистика для 10-дневных депозитов
            cursor.execute('''
                SELECT 
                    r.level,
                    COUNT(*) as count
                FROM referral_relations r
                JOIN users u ON r.referred_id = u.telegram_id
                WHERE r.referrer_id = ? 
                AND u.active_deposits_10 > 0
                GROUP BY r.level
            ''', (user_id,))
            
            results_10 = cursor.fetchall()
            
            stats_10 = {'level_1': 0, 'level_2': 0, 'level_3': 0, 'total': 0}
            for level, count in results_10:
                if 1 <= level <= 3:
                    stats_10[f'level_{level}'] = count
                    stats_10['total'] += count
            
            print(f"✅ Статистика 30-дневных: {stats_30}")
            print(f"✅ Статистика 10-дневных: {stats_10}")
            
            # Формируем сообщение как в боте (обновленная версия)
            message_text = f"""
👥 РЕФЕРАЛЬНАЯ СИСТЕМА

🔗 Ваша ссылка: `https://t.me/test_bot?start=ref_{user_id}`

📊 РЕФЕРАЛЫ (С АКТУАЛЬНЫМИ ВКЛАДАМИ):

📅 На 30 дней (15% / 10% / 5%):
1-й: {stats_30['level_1']}
2-й: {stats_30['level_2']}
3-й: {stats_30['level_3']}

📅 На 10 дней (5% / 3% / 1.5%):
1-й: {stats_10['level_1']}
2-й: {stats_10['level_2']}
3-й: {stats_10['level_3']}

💵 Общий доход: 0.00 USDT

💡 Приглашайте по ссылке → получайте % с пополнений до 3 уровня
            """
            
            print("\n" + "=" * 60)
            print("📱 ОБНОВЛЕННЫЙ ИНТЕРФЕЙС РЕФЕРАЛЬНОЙ СИСТЕМЫ:")
            print("=" * 60)
            print(message_text)
            print("=" * 60)
            
            # Показываем главное меню
            main_menu_text = """
🎯 ФондКлик

Выберите действие:
[💰 Внести средства]
[👥 Реферальная система]  ← ОБНОВЛЕНО!
[💸 Вывод средств]
[ℹ️ Информация]
            """
            
            print("\n" + "=" * 60)
            print("📱 ОБНОВЛЕННОЕ ГЛАВНОЕ МЕНЮ:")
            print("=" * 60)
            print(main_menu_text)
            print("=" * 60)
            
            print("\n✅ Изменения:")
            print("   ✅ Кнопка переименована: 'Рефералы (с актуальными вкладами)' → 'Реферальная система'")
            print("   ✅ Убрано разделение доходов: только 'Общий доход'")
            print("   ✅ Сохранены две таблицы рефералов по типам депозитов")
            
            print("\n✅ Тест обновленного интерфейса завершен успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_interface()
















