import logging
import os
import random

from dotenv import load_dotenv

from telegram_logger import TelegramLogsHandler
from questions import get_questions, get_answer

import redis

import telegram
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)


load_dotenv()
database_host = os.getenv('REDIS_HOST')
database_port = os.getenv('REDIS_PORT')
database_username = os.getenv('REDIS_USERNAME')
database_password = os.getenv('REDIS_PASSWORD')
creds_provider = redis.UsernamePasswordCredentialProvider(database_username, database_password)
database = redis.Redis(
    host=database_host,
    port=int(database_port),
    credential_provider=creds_provider,
    decode_responses=True
)
database.ping()

logger = logging.getLogger('Logger')

ANSWER, QUESTION = range(2)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    keyboard = [
        ['Новый вопрос','Сдаться'],
        ['Мой счёт']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text('Здравствуйте!', reply_markup=reply_markup)

    return QUESTION


def handle_new_question_request(update: Update, context: CallbackContext) -> None:
    print('new_question')
    question = random.choice(get_questions())
    print(question)
    database.set(update.message.chat_id, question[0])
    update.message.reply_text(question[0])

    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext) -> None:
    print('check_answer')
    question = database.get(update.message.chat_id)
    answer = get_answer(question)
    if answer == update.message.text:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»')
        return QUESTION
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return ANSWER


def handle_surrender(update: Update, context: CallbackContext) -> None:
    print('surrender')
    question = database.get(update.message.chat_id)
    if question:
        answer = get_answer(question)
        update.message.reply_text(f'Правильный ответ: {answer}')

        update.message.reply_text(f'Новый вопрос:')

    question = random.choice(get_questions())
    print(question)
    database.set(update.message.chat_id, question[0])
    update.message.reply_text(question[0])

    return ANSWER


def cancel(update):
    user = update.message.from_user
    update.message.reply_text('Пока!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():
    tg_token = os.getenv('TELEGRAM_TOKEN')

    updater = Updater(tg_token, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            ANSWER: [
                MessageHandler(Filters.text('Сдаться'), handle_surrender),
                MessageHandler(Filters.text, handle_solution_attempt)
            ],

            QUESTION: [
                MessageHandler(Filters.text('Новый вопрос'), handle_new_question_request),
                MessageHandler(Filters.text('Сдаться'), handle_surrender),
            ]
        },

        # fallbacks=[MessageHandler(Filters.text('Новый вопрос'), handle_new_question_request)]
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    try:
        updater.start_polling()
        updater.idle()
    except requests.exceptions.HTTPError as err:
        logger.warning(f'Ошибка!\n{err}')


if __name__ == '__main__':
    main()
