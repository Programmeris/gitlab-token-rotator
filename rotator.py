"""Used modules"""
import enum
import gitlab
import requests
import argparse
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

def main():
    """Simple script which rotate GitLab access tokens and send result to Telegram."""
    try:
        parser = argparse.ArgumentParser(
                        prog='script for rotate GitLab access tokens',
                        description='script for rotate GitLab access tokens')

        parser.add_argument('--gitlab-url', required=True)
        parser.add_argument('--gitlab-token', required=True)
        parser.add_argument('--telegram-bot-token', required=True)
        parser.add_argument('--telegram-chat-id', required=True)

        args = parser.parse_args()

        telegram_message = "\U0001F525 FIRING \n"
        telegram_message += f"Host {args.gitlab_url} has issues with tokens:\n"
        telegram_message += "\n"

        telegram_message += check_and_rotate_tokens(args.gitlab_url, args.gitlab_token, TokenType.GROUP_ACCESS_TOKEN)
        telegram_message += check_and_rotate_tokens(args.gitlab_url, args.gitlab_token, TokenType.PROJECT_ACCESS_TOKEN)
        send_to_telegram(args.telegram_bot_token, args.telegram_chat_id, telegram_message)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")

class TokenType(enum.Enum):
    GROUP_ACCESS_TOKEN = 0,
    PROJECT_ACCESS_TOKEN = 1

def check_and_rotate_tokens(gitlab_url: str, gitlab_token : str, token_type: TokenType):
    """Function which rotate GitLab access tokens."""
    gl = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token)

    today_date = dt.today().strftime('%Y-%m-%d')
    parsed_today_date = dt.strptime(today_date, "%Y-%m-%d")

    gl_rest_objects = []
    debug_message=''
    first_message_word=''

    match token_type:
        case TokenType.GROUP_ACCESS_TOKEN:
            gl_rest_objects = gl.groups.list(all=True)
            first_message_word='Group'
        case TokenType.PROJECT_ACCESS_TOKEN:
            gl_rest_objects = gl.projects.list(all=True)
            first_message_word='Project'

    for gl_rest_object in gl_rest_objects:
        gl_rest_object_name = gl_rest_object.name
        gl_rest_objects_access_tokens = gl_rest_object.access_tokens.list()
        for gl_rest_object_access_token in gl_rest_objects_access_tokens:
            parsed_expired_at_date = dt.strptime(gl_rest_object_access_token.expires_at, "%Y-%m-%d")
            diff_date = abs((parsed_expired_at_date - parsed_today_date).days)
            message = f"{first_message_word} access token {gl_rest_object_access_token.name} from {first_message_word.lower()} {gl_rest_object_name} expires at {gl_rest_object_access_token.expires_at}. Rotating..."
            print(message)
            if parsed_expired_at_date < parsed_today_date or diff_date <= 30:
                new_token_expires_at = (parsed_today_date + relativedelta(years=1)).strftime('%Y-%m-%d')
                gl_rest_object_access_token.rotate(expires_at=new_token_expires_at)
                debug_message += message
                debug_message += "\n"

    return debug_message

def send_to_telegram(telegram_bot_token: str, telegram_chat_id: str, telegram_message: str):
    """Function which send message to Telegram."""
    send_url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'

    if telegram_message.count('\n') >= 4:
        if len(telegram_message) > 4096:
            divided_telegram_message = divide_telegram_message(telegram_message)
            requests.post(send_url, json={'chat_id': telegram_chat_id, 'text': divided_telegram_message[0]}, timeout=10)
            requests.post(send_url, json={'chat_id': telegram_chat_id, 'text': divided_telegram_message[1]}, timeout=10)
        else:
            requests.post(send_url, json={'chat_id': telegram_chat_id, 'text': telegram_message}, timeout=10)
    else:
        print('No token issues.')

def divide_telegram_message(telegram_message: str):
    """Function which divide Telegram message on two parts."""
    first_message_part = ''
    second_message_part = ''

    for i in range(0, 2048):
        first_message_part += telegram_message[i]

    for i in range(2048, len(telegram_message)):
        second_message_part += telegram_message[i]

    message_parts = [first_message_part, second_message_part]
    return message_parts

if __name__ == '__main__':
    main()
