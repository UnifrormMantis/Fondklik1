#!/usr/bin/env python3
"""
Скрипт для исправления отступов в bot_final.py
"""

def fix_indentation():
    with open('bot_final.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for line in lines:
        # Исправляем неправильные отступы
        if line.startswith('                        cursor.execute'):
            line = '            ' + line.strip() + '\n'
        elif line.startswith('                        logger.'):
            line = '                        ' + line.strip() + '\n'
        elif line.startswith('                message_text +='):
            line = '            ' + line.strip() + '\n'
        elif line.startswith('                user_name ='):
            line = '            ' + line.strip() + '\n'
        elif line.startswith('                username ='):
            line = '            ' + line.strip() + '\n'
        elif line.startswith('                if days_remaining not in days_dict:'):
            line = '                ' + line.strip() + '\n'
        elif line.startswith('                days_dict[days_remaining]['):
            line = '                ' + line.strip() + '\n'
        elif line.startswith('                # Получаем оригинальную сумму'):
            line = '                ' + line.strip() + '\n'
        elif line.startswith('                original_amount_for_type ='):
            line = '                ' + line.strip() + '\n'
        
        fixed_lines.append(line)
    
    with open('bot_final.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Отступы исправлены!")

if __name__ == "__main__":
    fix_indentation()








