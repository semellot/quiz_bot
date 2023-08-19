import logging
import os
import requests

from dotenv import load_dotenv
import redis
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id


logger = logging.getLogger('Logger for vk_bot')


def get_keybord():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()


def handle_start(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=get_keybord(),
        message='Приветствую! Для участия в квизе нажми «Новый вопрос»! Удачи!',
    )


def handle_new_question_request(event, vk_api, database):
    question = database.randomkey()
    answer = database.get(question)
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=get_keybord(),
        message=question,
    )
    return answer


def handle_right_solution(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=get_keybord(),
        message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
    )


def handle_wrong_solution(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=get_keybord(),
        message='Неправильно… Попробуешь ещё раз?',
    )


def handle_surrender(event, vk_api, database, answer):
    message=f'Правильный ответ: {answer} \n\n Новый вопрос:\n'
    question = database.randomkey()
    answer = database.get(question)
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=get_keybord(),
        message=message+question,
    )
    return answer


def main() -> None:
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

    vk_group_token = os.getenv('VK_GROUP_TOKEN')
    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    try:
        answer = ''
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == "Сдаться":
                    if answer:
                        answer = handle_surrender(event, vk_api, database, answer)
                    else:
                        answer = handle_new_question_request(event, vk_api, database)
                elif event.text == "Новый вопрос":
                    answer = handle_new_question_request(event, vk_api, database)
                elif answer:
                    if answer == event.text:
                        handle_right_solution(event, vk_api)
                    else:
                        handle_wrong_solution(event, vk_api)
                else:
                    handle_start(event, vk_api)
    except requests.exceptions.HTTPError as err:
        logger.warning(f'Ошибка!\n{err}')


if __name__ == '__main__':
    main()
