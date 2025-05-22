from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_credentials(user_id: int):
    """
    Отримує або створює об'єкт облікових даних для Google Calendar API для конкретного користувача.

    Якщо токен існує локально — використовує його.
    Якщо ні — запускає OAuth flow для отримання нового токена і зберігає його у файл.

    Args:
        user_id (int): Унікальний ID користувача Telegram.

    Returns:
        Credentials: об'єкт авторизації Google API.
    """
    token_path = f"token_{user_id}.pkl"

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            return pickle.load(token)

    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)

    with open(token_path, "wb") as token:
        pickle.dump(creds, token)

    return creds
