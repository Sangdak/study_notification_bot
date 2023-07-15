import time

from environs import Env
import requests
import telegram


def main():
    env = Env()
    env.read_env(override=True)

    dvmn_api_token = env.str('DVMN_TOKEN')
    api_long_polling_url = 'https://dvmn.org/api/long_polling/'
    tg_bot_token = env.str('TG_TOKEN')
    tg_chat_id = env.str('TG_CHAT')

    bot = telegram.Bot(token=tg_bot_token)

    headers = {'Authorization': f'Token {dvmn_api_token}'}
    params = {}

    while True:
        try:
            response = requests.get(url=api_long_polling_url, headers=headers, params=params)
            response.raise_for_status()

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            print(f'Some problem with connection. Wait 60 seconds before repeat.')
            time.sleep(60)

        answer = response.json()

        if answer['status'] == 'found':
            params['timestamp'] = answer['last_attempt_timestamp']
            if answer['new_attempts'][0]['is_negative']:
                task_status = 'Работа требует доработки.'
            else:
                task_status = 'Работа принята.'

            bot.send_message(
                chat_id=tg_chat_id,
                text=f'Преподаватель проверил работу: \"{answer["new_attempts"][0]["lesson_title"]}\".\n'
                     f'{answer["new_attempts"][0]["lesson_url"]}\n'
                     f'{task_status}',
            )

        elif answer['status'] == 'timeout':
            params['timestamp'] = answer['timestamp_to_request']


if __name__ == '__main__':
    main()
