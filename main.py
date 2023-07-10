import logging
import os
import telegram

from dotenv import load_dotenv

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


logger = logging.getLogger('Logger')

class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_token, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = telegram.Bot(token=tg_token)

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def get_question_answer():
    with open('quiz-questions/1vs1200.txt', 'r', encoding='KOI8-R') as quiz_file:
      quiz_content = quiz_file.read()

    questions = []

    for quiz in quiz_content.split('\n\n\n'):
        if quiz == '':
            continue
        quiz = quiz[quiz.find('Вопрос'):]
        quiz_elements = quiz.split('\n\n')
        print(quiz_elements)
        question = quiz_elements[0][quiz_elements[0].find('\n'):]
        answer = quiz_elements[1][quiz_elements[1].find('\n'):]
        questions.append({
            'Вопрос': question,
            'Ответ': answer
        })

    print(questions)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text('Здравствуйте!')


def send_answer(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


def main():
    load_dotenv()
    tg_bot_token = os.getenv("TG_BOT_TOKEN")

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, send_answer))

    try:
        updater.start_polling()
        updater.idle()
    except requests.exceptions.HTTPError as err:
        logger.warning(f'Ошибка!\n{err}')


if __name__ == '__main__':
    main()
