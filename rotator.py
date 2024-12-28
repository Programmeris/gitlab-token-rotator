from datetime import datetime as dt
import enum
import gitlab
import requests

def main():
    GITLAB_URL=
    ACCESS_TOKEN=
    TELEGRAM_BOT_TOKEN=
    TELEGRAM_CHAT_ID=

    telegram_message = "\U0001F525 FIRING \n"
    telegram_message += f"Host {GITLAB_URL} has issues with tokens:\n"
    telegram_message += "\n"

    try:
        telegram_message += check_and_rotate_tokens(GITLAB_URL, ACCESS_TOKEN, TokenType.GroupAccessToken)
        telegram_message += check_and_rotate_tokens(GITLAB_URL, ACCESS_TOKEN, TokenType.ProjectAccessToken)
        send_to_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, telegram_message)
    except Exception:
        print("Error!")

class TokenType(enum.Enum):
    GroupAccessToken = 0,
    ProjectAccessToken = 1

def check_and_rotate_tokens(gitlab_url: str, gitlab_token : str, token_type: TokenType):

    gl = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token)

    today_date = dt.today().strftime('%Y-%m-%d')
    parsed_today_date = dt.strptime(today_date, "%Y-%m-%d")

    glRestObjects = []
    debug_message=''
    first_message_word=''

    match token_type:
        case TokenType.GroupAccessToken:
            glRestObjects = gl.groups.list(all=True)
            first_message_word='Group'
        case TokenType.ProjectAccessToken:
            glRestObjects = gl.projects.list(all=True)
            first_message_word='Project'

    for glRestObject in glRestObjects:
        gl_rest_object_name = glRestObject.name
        gl_rest_objects_access_tokens = glRestObject.access_tokens.list()
        for gl_rest_object_access_token in gl_rest_objects_access_tokens:
            parsed_expired_at_date = dt.strptime(gl_rest_object_access_token.expires_at, "%Y-%m-%d")
            diff_date = abs((parsed_expired_at_date - parsed_today_date).days)
            message = f"{first_message_word} access token {gl_rest_object_access_token.name} from {first_message_word.lower()} {gl_rest_object_name} expires at {gl_rest_object_access_token.expires_at}"
            print(message)
            if parsed_expired_at_date < parsed_today_date or diff_date <= 7:
                debug_message += message
                debug_message += "\n"

    return debug_message

def send_to_telegram(telegram_bot_token: str, telegram_chat_id: str, telegram_message: str):
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
