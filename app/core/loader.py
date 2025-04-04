from app.core.config import settings

PUBLIC_KEY = None

if settings.JWT_VERIFICATION:
    with open(settings.PUBLISHABLE_KEY_PATH, 'r') as file:
        PUBLIC_KEY = file.read()
