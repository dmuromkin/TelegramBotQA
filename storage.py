import aiosqlite

DB_NAME = 'data/quiz_bot.db'

async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, score INTEGER, prevScore INTEGER)')
        # Сохраняем изменения
        await db.commit()

async def update_seesion(user_id, index, score):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
         # Получаем запись для заданного пользователя
        async with db.execute('SELECT * FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                prevScore = results[3]
                await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, score, prevScore) VALUES (?, ?, ?, ?)', (user_id, index, score, prevScore))
            else:
                await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, score, prevScore) VALUES (?, ?, ?, ?)', (user_id, index, score, 0))
            # Сохраняем изменения
            await db.commit()
        
async def get_session(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT * FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results
            else:
                return [user_id, 0, 0, 0]
            
async def update_prevScore(user_id, score):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, prevScore) VALUES (?, ?)', (user_id, score))
        # Сохраняем изменения
        await db.commit()