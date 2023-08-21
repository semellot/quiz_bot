import argparse
import json
import os

import redis
from dotenv import load_dotenv


def get_questions(quiz_file):
    with open(quiz_file, 'r', encoding='KOI8-R') as file:
        quiz_content = file.read()

    questions = []

    for quiz in quiz_content.split('\n\n\n'):
        if 'Вопрос' in quiz:
            quiz = quiz[quiz.find('Вопрос'):]
            quiz_elements = quiz.split('\n\n')
            for quiz_element in quiz_elements:
                if quiz_element.startswith('Вопрос'):
                    question = quiz_element[quiz_element.find('\n'):]
                if quiz_element.startswith('Ответ'):
                    answer = quiz_element[quiz_element.find('\n'):]
            questions.append([question.replace('\n', ' '), answer.replace('\n', ' ')])
    return questions


def main():
    load_dotenv()
    database_host = os.getenv('REDIS_HOST')
    database_port = os.getenv('REDIS_PORT')
    database_username = os.getenv('REDIS_USERNAME')
    database_password = os.getenv('REDIS_PASSWORD')

    default_quiz_file = 'faq-example.txt'
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Файл с вопросами и ответами', nargs='?', default=default_quiz_file)
    received_args = parser.parse_args()
    quiz_file = received_args.file

    creds_provider = redis.UsernamePasswordCredentialProvider(database_username, database_password)
    database = redis.Redis(
        host=database_host,
        port=int(database_port),
        credential_provider=creds_provider,
        decode_responses=True
    )
    database.ping()

    questions = get_questions(quiz_file)

    for question, answer in questions:
        database.mset({question: answer})


if __name__ == '__main__':
    main()
