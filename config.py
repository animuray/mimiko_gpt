import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
AI_TOKEN = os.getenv('DS_TOKEN')
API_ENDPOINT = os.getenv('API_ENDPOINT')

CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')


PROFILES = {
    'DEFAULT_PROFILE': "Дефолтный профиль",
    'junior_profile' : "junior profile",
}





