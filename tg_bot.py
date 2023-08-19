import logging
import os
import requests

from dotenv import load_dotenv
import redis
import telegram
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)


logger = logging.getLogger('Logger')

ANSWER, QUESTION = range(2)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    keyboard = [
        ['Новый вопрос','Сдаться'],
        ['Мой счёт']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text('Приветствую! Для участия в квизе нажми «Новый вопрос»! Удачи!', reply_markup=reply_markup)

    return QUESTION


def handle_new_question_request(update: Update, context: CallbackContext) -> None:
    database = context.bot_data['database']
    question = database.randomkey()
    context.user_data['answer'] = database.get(question)
    update.message.reply_text(question)

    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext) -> None:
    answer = context.user_data['answer']
    if answer == update.message.text:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»')
        return QUESTION
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return ANSWER


def handle_surrender(update: Update, context: CallbackContext) -> None:
    database = context.bot_data['database']
    answer = context.user_data['answer']
    if answer:
        update.message.reply_text(f'Правильный ответ: {answer}')
        update.message.reply_text(f'Новый вопрос:')

    question = database.randomkey()
    context.user_data['answer'] = database.get(question)
    update.message.reply_text(question)

    return ANSWER


def cancel(update):
    user = update.message.from_user
    update.message.reply_text('Пока!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():
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

    tg_token = os.getenv('TELEGRAM_TOKEN')

    updater = Updater(tg_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['database'] = database

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            ANSWER: [
                MessageHandler(Filters.text('Новый вопрос'), handle_new_question_request),
                MessageHandler(Filters.text('Сдаться'), handle_surrender),
                MessageHandler(Filters.text, handle_solution_attempt)
            ],

            QUESTION: [
                MessageHandler(Filters.text('Новый вопрос'), handle_new_question_request),
                MessageHandler(Filters.text('Сдаться'), handle_surrender),
            ]
        },

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
