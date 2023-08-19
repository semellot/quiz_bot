import argparse
import json
import os

import redis
from dotenv import load_dotenv


def fill_database(quiz_file, database_host, database_port, database_username, database_password):
    creds_provider = redis.UsernamePasswordCredentialProvider(database_username, database_password)
    database = redis.Redis(
        host=database_host,
        port=int(database_port),
        credential_provider=creds_provider,
        decode_responses=True
    )
    database.ping()

    with open(quiz_file, 'r', encoding='KOI8-R') as file:
        quiz_content = file.read()

    questions = []

    for quiz in quiz_content.split('\n\n\n'):
        if 'Вопрос' in quiz:
            quiz = quiz[quiz.find('Вопрос'):]
            quiz_elements = quiz.split('\n\n')
            question = quiz_elements[0][quiz_elements[0].find('\n'):]
            answer = quiz_elements[1][quiz_elements[1].find('\n'):]
            questions.append([question.replace('\n', ''), answer.replace('\n', '')])

    for question, answer in questions:
        print(question, answer)
        database.mset({question: answer})


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

    fill_database(
        quiz_file,
        database_host,
        database_port,
        database_username,
        database_password
    )


if __name__ == '__main__':
    main()
