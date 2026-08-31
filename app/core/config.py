from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Пути
    PROJECT_PATH: str = "."  # По умолчанию текущая папка
    OUTPUT_PATH: str = "mindmap.html"
    
    # AI Настройки (Ollama)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama:7b"  # Или "mistral", "llama3"
    
    # Фильтры
    ALLOWED_EXTENSIONS: List[str] = [
        ".py", ".js", ".ts", ".md", ".go", ".rs",
        ".ipynb",  # Jupyter Notebook
        ".java", ".cpp", ".c", ".h", ".hpp"
    ]
    MAX_FILE_SIZE_KB: int = 5000  # Увеличил до 5 МБ для Jupyter
    
    class Config:
        env_file = ".env"

settings = Settings()