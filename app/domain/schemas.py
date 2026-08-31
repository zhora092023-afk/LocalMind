# Файл app/domain/schemas.py (Модели данных)

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"

class FileInfo(BaseModel):
    """Входной файл для анализа"""
    path: str
    content: str
    file_type: FileType
    size_kb: float

class CodeEntity(BaseModel):
    """Сущность, найденная в коде (класс, функция, зависимость)"""
    name: str
    entity_type: str  # "class", "function", "import", "endpoint"
    description: str
    dependencies: List[str] = Field(default_factory=list)

class ProjectMindMap(BaseModel):
    """Выходная структура для визуализации"""
    project_name: str
    total_files: int
    total_lines: int
    entities: List[CodeEntity]
    connections: List[Dict[str, str]]  # [{"from": "main.py", "to": "utils.py"}]
    summary: str  # Краткий AI-вывод о проекте
    generated_at: datetime = Field(default_factory=datetime.now)