import os


def get_questions():
    with open(f'{os.path.dirname(__file__)}/faq-example.txt', 'r', encoding='KOI8-R') as quiz_file:
      quiz_content = quiz_file.read()

    questions = []

    for quiz in quiz_content.split('\n\n\n'):
        if 'Вопрос' in quiz:
            quiz = quiz[quiz.find('Вопрос'):]
            quiz_elements = quiz.split('\n\n')
            question = quiz_elements[0][quiz_elements[0].find('\n'):]
            answer = quiz_elements[1][quiz_elements[1].find('\n'):]
            questions.append([question.replace('\n', ''), answer.replace('\n', '')])

    return questions


def get_answer(user_question):
    questions = get_questions()
    for question in questions:
        if user_question in question:
            return question[1]
