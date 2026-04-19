"""Entry point for Hugging Face Spaces and local development."""

import os
from src.ui.app import create_app
from src.config import settings

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=settings.port,
        share=False,
        show_error=True,
    )
else:
    # HF Spaces calls create_app() at import time
    app = create_app()

