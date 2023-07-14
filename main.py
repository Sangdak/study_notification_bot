from pprint import pprint

from environs import Env
import requests
import telegram

env = Env()
env.read_env(override=True)


DVMN_API_TOKEN = env.str('DVMN_TOKEN')
API_LONG_POLLING_URL = 'https://dvmn.org/api/long_polling/'
TG_BOT_TOKEN = env.str('TG_TOKEN')
TG_CHAT_ID = env.str('TG_CHAT')


def main():
    bot = telegram.Bot(token=TG_BOT_TOKEN)

    headers = {'Authorization': f'Token {DVMN_API_TOKEN}'}
    params = {}

    while True:
        try:
            response = requests.get(url=API_LONG_POLLING_URL, headers=headers, params=params)
            response.raise_for_status()

        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            continue

        answer = response.json()

        if answer['status'] == 'found':
            params['timestamp'] = answer['last_attempt_timestamp']
            if answer['new_attempts'][0]['is_negative']:
                task_status = 'Работа требует доработки.'
            else:
                task_status = 'Работа принята.'

            bot.send_message(
                chat_id=TG_CHAT_ID,
                text=f'Преподаватель проверил работу: \"{answer["new_attempts"][0]["lesson_title"]}\".\n'
                     f'{answer["new_attempts"][0]["lesson_url"]}\n'
                     f'{task_status}',
            )

        elif answer['status'] == 'timeout':
            params['timestamp'] = answer['timestamp_to_request']


if __name__ == '__main__':
    main()
