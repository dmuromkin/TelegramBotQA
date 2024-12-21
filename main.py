import asyncio
import logging
import storage
import bot_controller

# Включение логов
logging.basicConfig(level=logging.INFO)


# Запуск процесса поллинга новых апдейтов
async def main():
    # Запуск создания таблицы базы данных
    await storage.create_table()
    # Запуск контроллера бота
    await bot_controller.init()

if __name__ == "__main__":
    asyncio.run(main())