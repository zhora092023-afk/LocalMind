# Файл app/interfaces.py (Абстрактные классы — контракт для всех агентов)

from abc import ABC, abstractmethod
from typing import List, AsyncIterator
from app.domain.schemas import FileInfo, ProjectMindMap, CodeEntity
from typing import Dict, Union

class IFileReader(ABC):
    """Ответственность: Обход папки и чтение файлов"""
    
    @abstractmethod
    async def scan_directory(self, root_path: str, extensions: List[str]) -> AsyncIterator[FileInfo]:
        """Асинхронно обходит папку, отдавая файлы по одному (чтобы не грузить память)"""
        pass
    
    @abstractmethod
    def get_total_stats(self) -> Dict[str, Union[int, float]]:
        """Возвращает статистику: кол-во файлов, общий размер"""
        pass

class IAnalyzer(ABC):
    """Ответственность: Анализ кода через AI (локально или в облаке)"""
    
    @abstractmethod
    async def extract_entities(self, file_content: str, file_type: str) -> List[CodeEntity]:
        """Извлекает классы, функции, импорты из одного файла"""
        pass
    
    @abstractmethod
    async def generate_summary(self, all_entities: List[CodeEntity]) -> str:
        """Генерирует общее описание проекта на основе всех сущностей"""
        pass

class IMindmapGenerator(ABC):
    """Ответственность: Визуализация результатов в HTML/Markdown"""
    
    @abstractmethod
    async def render_html(self, mindmap: ProjectMindMap) -> str:
        """Возвращает строку с HTML-кодом для интерактивной карты"""
        pass
    
    @abstractmethod
    async def save_to_file(self, html_content: str, output_path: str) -> None:
        """Сохраняет HTML на диск"""
        pass