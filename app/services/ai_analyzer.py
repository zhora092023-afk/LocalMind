import re
import json
from typing import List
from app.interfaces import IAnalyzer
from app.domain.schemas import CodeEntity
from app.core.config import settings
import httpx
from app.core.config import settings

class AIAnalyzer(IAnalyzer):
    """Агент для анализа кода с использованием локального AI или регулярных выражений"""
    async def analyze_with_ollama(self, code: str, context: str = "") -> dict:
        """Отправляет код в Ollama для анализа"""
        if not settings.OLLAMA_URL:
            return {"error": "Ollama не настроен"}
        
        prompt = f"""
Проанализируй следующий код и ответь в формате JSON:
{{
    "purpose": "краткое описание назначения кода (1 предложение)",
    "complexity": "low/medium/high",
    "patterns": ["список", "паттернов", "проектирования"],
    "improvements": ["список", "рекомендаций", "по улучшению"],
    "dependencies": ["список", "основных", "зависимостей"]
}}

Код:
{code[:3000]}  # Ограничиваем для экономии токенов
"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=30.0
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_entities(self, file_content: str, file_type: str) -> List[CodeEntity]:
        # Если файл .ipynb — мы уже извлекли код, он просто многострочный
        if file_type == "python":
            return self._parse_python(file_content)
        elif file_type == "javascript":
            return self._parse_javascript(file_content)
        else:
            return []
    
    async def generate_summary(self, all_entities: List[CodeEntity]) -> str:
        """Генерирует краткое описание проекта на основе всех сущностей"""
        if not all_entities:
            return "Проект не содержит распознаваемых сущностей"
        
        # Собираем статистику
        total_classes = sum(1 for e in all_entities if e.entity_type == "class")
        total_functions = sum(1 for e in all_entities if e.entity_type == "function")
        total_imports = sum(1 for e in all_entities if e.entity_type == "import")
        
        summary = f"""Проект содержит:
- {total_classes} классов
- {total_functions} функций
- {total_imports} импортов

Основные компоненты: {', '.join([e.name[:20] for e in all_entities[:5]])}...
"""
        return summary
    
    def _parse_python(self, content: str) -> List[CodeEntity]:
        """Парсит Python-файл с помощью регулярных выражений"""
        entities = []
        
        # Ищем классы
        class_pattern = r'^class\s+(\w+)\s*(?:\(.*\))?:'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            entities.append(CodeEntity(
                name=match.group(1),
                entity_type="class",
                description=f"Класс {match.group(1)}",
                dependencies=[]
            ))
        
        # Ищем функции
        func_pattern = r'^def\s+(\w+)\s*\([^)]*\):'
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            entities.append(CodeEntity(
                name=match.group(1),
                entity_type="function",
                description=f"Функция {match.group(1)}",
                dependencies=[]
            ))
        
        # Ищем импорты
        import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(\S+)'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            module = match.group(1) or match.group(2)
            entities.append(CodeEntity(
                name=module,
                entity_type="import",
                description=f"Импорт {module}",
                dependencies=[]
            ))
        
        return entities
    
    def _parse_javascript(self, content: str) -> List[CodeEntity]:
        """Парсит JavaScript/TypeScript файл"""
        entities = []
        
        # Ищем классы
        class_pattern = r'class\s+(\w+)\s*(?:extends\s+\w+)?\s*{'
        for match in re.finditer(class_pattern, content):
            entities.append(CodeEntity(
                name=match.group(1),
                entity_type="class",
                description=f"Класс {match.group(1)}",
                dependencies=[]
            ))
        
        # Ищем функции
        func_pattern = r'(?:function\s+(\w+)|(\w+)\s*=\s*function|(\w+)\s*\([^)]*\)\s*{)'
        for match in re.finditer(func_pattern, content):
            name = match.group(1) or match.group(2) or match.group(3)
            if name:
                entities.append(CodeEntity(
                    name=name,
                    entity_type="function",
                    description=f"Функция {name}",
                    dependencies=[]
                ))
        
        return entities