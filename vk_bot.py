import logging
import os
import random
import requests

from telegram_logger import TelegramLogsHandler

from dotenv import load_dotenv

from questions import get_questions, get_answer

import redis

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

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

logger = logging.getLogger('Logger for vk_bot')


def send_keybord():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()


def handle_new_question_request(event, vk_api):
    question = random.choice(get_questions())
    database.set(event.user_id, question[0])
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=send_keybord(),
        message=question[0],
    )

def handle_solution_attempt(event, vk_api):
    question = database.get(event.user_id)
    answer = get_answer(question)
    if answer == event.text:
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            keyboard=send_keybord(),
            message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            keyboard=send_keybord(),
            message='Неправильно… Попробуешь ещё раз?',
        )


def handle_surrender(event, vk_api):
    question = database.get(event.user_id)
    if question:
        answer = get_answer(question)
        message=f'Правильный ответ: {answer} \n\n Новый вопрос:\n'

    question = random.choice(get_questions())
    database.set(event.user_id, question[0])
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=send_keybord(),
        message=message+question[0],
    )


def main() -> None:
    vk_group_token = os.getenv('VK_GROUP_TOKEN')
    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == "Сдаться":
                    handle_surrender(event, vk_api)
                if event.text == "Новый вопрос":
                    handle_new_question_request(event, vk_api)
                else:
                    handle_solution_attempt(event, vk_api)
    except requests.exceptions.HTTPError as err:
        logger.warning(f'Ошибка!\n{err}')


if __name__ == '__main__':
    main()
