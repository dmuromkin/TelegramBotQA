from aiogram import types
from aiogram.filters.command import Command
from aiogram.filters.callback_data import CallbackData
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from api_token import API_TOKEN
import storage
from data.quiz_data import QUIZ_DATA

dp = Dispatcher()
# Объект бота
bot = Bot(token=API_TOKEN)

# Описание колюэка для inline кнопок
class AnswerCallback(CallbackData, prefix="callback"):
    userAnswerKey: int
    isValid: bool

def generate_options_keyboard(answer_options, right_answer):
  # Создаем сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()
    key = 0
    # В цикле создаем Callback-кнопки
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            # Текст на кнопках соответствует вариантам ответов
            text=option,
            # Присваиваем данные для колбэк запроса.
            callback_data=AnswerCallback(userAnswerKey=key, isValid=option == right_answer).pack()
        ))
        key += 1
    
    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()


async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    session = await storage.get_session(user_id)
    current_question_index = session[1]
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = QUIZ_DATA[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = QUIZ_DATA[current_question_index]['options']
    
    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{QUIZ_DATA[current_question_index]['question']}", reply_markup=kb)
    

async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await storage.update_seesion(user_id, current_question_index, 0)
    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Логика обработки команды /start
        # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")
    # Запускаем новый квиз
    await new_quiz(message)    
        
@dp.callback_query(AnswerCallback.filter(F.isValid == True))
async def right_answer(callback: types.CallbackQuery, callback_data: AnswerCallback):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    
    # Получение текущего вопроса для данного пользователя
    session = await storage.get_session(callback.from_user.id)
    current_question_index = session[1]
    current_score = session[2]
    
    user_answer = QUIZ_DATA[current_question_index]['options'][callback_data.userAnswerKey]
    await callback.message.reply("Ваш ответ: " + user_answer)
    # Отправляем в чат сообщение, что ответ верный
    await callback.message.answer("Верно!")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    current_score += 1
    await storage.update_seesion(callback.from_user.id, current_question_index, current_score)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(QUIZ_DATA):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        await storage.update_prevScore(callback.from_user.id, current_score)
        prevScore = session[3]
        message = "Вы набрали " + str(current_score) + " очков(a). Предыдущий результат: " + str(prevScore)
        await callback.message.answer(message)
        '''highScore = session[3]
        if(highScore is None or current_score > highScore):
            await callback.message.answer("Новый рекорд: " + str(current_score) + " очков!")
            await storage.update_highScore(callback.from_user.id, current_score)
        else:
            await callback.message.answer("Вы набрали " + str(current_score) + " очков Рекорд: " + str(highScore))'''
            
        
@dp.callback_query(AnswerCallback.filter(F.isValid == False))
async def wrong_answer(callback: types.CallbackQuery, callback_data: AnswerCallback):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    #await callback.message.reply("Ваш ответ: " + callback_data.userMessage)
    # Получение текущего вопроса для данного пользователя
    session = await storage.get_session(callback.from_user.id)
    current_question_index = session[1]
    current_score = session[2]

    correct_option = QUIZ_DATA[current_question_index]['correct_option']
    user_answer = QUIZ_DATA[current_question_index]['options'][callback_data.userAnswerKey]
    await callback.message.reply("Ваш ответ: " + user_answer)

    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Неправильно. Правильный ответ: {QUIZ_DATA[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await storage.update_seesion(callback.from_user.id, current_question_index, current_score)
    
    # Проверяем достигнут ли конец квиза
    if current_question_index < len(QUIZ_DATA):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        await storage.update_prevScore(callback.from_user.id, current_score)
        prevScore = session[3]
        message = "Вы набрали " + str(current_score) + " очков(a). Предыдущий результат: " + str(prevScore)
        await callback.message.answer(message)
        
        
async def init():
   await dp.start_polling(bot)