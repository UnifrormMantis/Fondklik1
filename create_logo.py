#!/usr/bin/env python3
"""
Создание логотипа ФондКлик
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_logo():
    """Создать логотип ФондКлик"""
    
    # Размеры изображения
    width, height = 400, 100
    
    # Создаем черный фон
    img = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(img)
    
    # Рисуем галочку
    checkmark_points = [
        (30, 50),   # Начало
        (50, 70),   # Середина
        (80, 30)    # Конец
    ]
    
    # Рисуем галочку белым цветом, толщина 8
    draw.line(checkmark_points, fill='white', width=8)
    
    # Добавляем текст "ФондКлик"
    try:
        # Пытаемся использовать системный шрифт
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
    except:
        try:
            # Альтернативный шрифт
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            # Используем стандартный шрифт
            font = ImageFont.load_default()
    
    # Позиция текста (справа от галочки)
    text_x = 100
    text_y = 30
    
    # Рисуем текст белым цветом
    draw.text((text_x, text_y), "ФондКлик", fill='white', font=font)
    
    # Сохраняем изображение
    img.save('logo.png')
    print("✅ Логотип создан: logo.png")

if __name__ == "__main__":
    create_logo()















