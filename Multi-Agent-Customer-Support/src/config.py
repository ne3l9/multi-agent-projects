import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()],
)


class Settings:
    model_name: str = os.getenv("MODEL_NAME", "mistral")
    temperature: float = float(os.getenv("TEMPERATURE", "0"))
    port: int = int(os.getenv("PORT", "7860"))
    app_title: str = "Music Store Assistant"
    app_description: str = (
        "Welcome! I can help you explore our music catalog, look up invoices, "
        "and find your purchase history. To access your account, please provide "
        "your Customer ID, email, or phone number."
    )


settings = Settings()
