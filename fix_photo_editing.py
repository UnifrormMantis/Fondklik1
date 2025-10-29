#!/usr/bin/env python3
"""
🔧 ИСПРАВИТЕЛЬ ОШИБКИ РЕДАКТИРОВАНИЯ ФОТО
==========================================
Исправляет все методы, которые пытаются редактировать сообщения с фото как текстовые
"""

import re

def fix_photo_editing():
    """Исправляет все методы редактирования фото"""
    
    # Читаем файл
    with open('bot_fondklik_correct.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ID фото логотипа
    logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
    
    # Список методов, которые нужно исправить
    methods_to_fix = [
        'show_deposit_options',
        'show_referral_info', 
        'show_my_deposits',
        'show_info',
        'show_referral_withdrawal'
    ]
    
    # Паттерн для поиска edit_message_text в методах
    pattern = r'(async def ({}).*?)(await update\.callback_query\.edit_message_text\(\s*text=([^,]+),\s*reply_markup=([^)]+)\))'.format('|'.join(methods_to_fix))
    
    def replace_edit_text(match):
        method_start = match.group(1)
        method_name = match.group(2)
        text_var = match.group(3)
        reply_markup_var = match.group(4)
        
        # Заменяем edit_message_text на edit_message_media
        replacement = f'{method_start}\n        # ID фото логотипа ФондКлик\n        logo_photo_id = "{logo_photo_id}"\n        \n        await update.callback_query.edit_message_media(\n            media=InputMediaPhoto(media=logo_photo_id, caption={text_var}),\n            reply_markup={reply_markup_var}\n        )'
        
        return replacement
    
    # Применяем замену
    new_content = re.sub(pattern, replace_edit_text, content, flags=re.MULTILINE | re.DOTALL)
    
    # Сохраняем исправленную версию
    with open('bot_fondklik_correct.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Исправления применены!")

if __name__ == "__main__":
    fix_photo_editing()








