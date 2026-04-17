#!/usr/bin/env python3
"""
WinYandexMusicRPC - Discord Rich Presence для Яндекс Музыки
Рефакторированная версия с модульной архитектурой
"""

import sys
import asyncio
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent))

from core.app_state import AppState
from core.presence_service import PresenceService
from utils.logger import setup_logger, get_logger
from utils.string_utils import print_colored_banner


def main():
    """Точка входа в приложение"""
    
    # Инициализация логирования
    setup_logger()
    logger = get_logger(__name__)
    
    try:
        # Печать баннера
        print_colored_banner()
        
        # Инициализация состояния приложения
        app_state = AppState()
        
        # Создание и запуск сервиса
        service = PresenceService(app_state)
        
        logger.info("Запуск WinYandexMusicRPC...")
        print_colored_banner()
        print("\n✅ Приложение запущено!")
        print("ℹ️  Rich Presence активен пока играет музыка")
        print("🎵 Слушайте Яндекс Музыку и наслаждайтесь!\n")
        
        # Запуск основного цикла
        asyncio.run(service.run())
        
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
        print("\n👋 До свидания!")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        print(f"\n❌ Произошла ошибка: {e}")
        print("💡 Проверьте логи для подробностей")
        sys.exit(1)


if __name__ == "__main__":
    main()
