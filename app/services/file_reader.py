import json
from typing import AsyncIterator, Dict, Union, List
from pathlib import Path
from collections import Counter
import aiofiles
from app.interfaces import IFileReader
from app.domain.schemas import FileInfo, FileType
from app.core.config import settings

class FileReader(IFileReader):
    def __init__(self):
        self._total_files = 0
        self._total_size_kb = 0.0
        self._extension_stats = Counter()

    async def scan_directory(self, root_path: str, extensions: List[str]) -> AsyncIterator[FileInfo]:
        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(f"Папка {root_path} не найдена")

        for file_path in root.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                # Считаем расширения
                self._extension_stats[file_path.suffix] += 1
                
                # Проверяем размер
                size_bytes = file_path.stat().st_size
                size_kb = size_bytes / 1024
                if size_kb > settings.MAX_FILE_SIZE_KB:
                    continue

                # Читаем содержимое
                content = await self._read_file_content(file_path)
                if content is None:
                    continue

                # Определяем тип файла
                file_type = self._get_file_type(file_path.suffix)

                yield FileInfo(
                    path=str(file_path),
                    content=content,
                    file_type=file_type,
                    size_kb=round(size_kb, 2)
                )

                self._total_files += 1
                self._total_size_kb += size_kb

    async def _read_file_content(self, file_path: Path) -> str | None:
        """Читает содержимое файла с учётом формата"""
        try:
            if file_path.suffix == ".ipynb":
                # Для Jupyter Notebook парсим JSON и извлекаем код
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    data = json.loads(await f.read())
                code_parts = []
                for cell in data.get("cells", []):
                    if cell.get("cell_type") in ["code", "markdown"]:
                        source = cell.get("source", [])
                        if isinstance(source, list):
                            code_parts.append("".join(source))
                        else:
                            code_parts.append(str(source))
                return "\n".join(code_parts)
            else:
                # Обычные текстовые файлы
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    return await f.read()
        except (UnicodeDecodeError, json.JSONDecodeError, Exception):
            # Если не удалось прочитать — пропускаем
            return None

    def get_total_stats(self) -> Dict[str, Union[int, float, Dict]]:
        return {
            "total_files": self._total_files,
            "total_size_kb": round(self._total_size_kb, 2),
            "extensions": dict(self._extension_stats)
        }
    
    def _get_file_type(self, extension: str) -> FileType:
        mapping = {
            ".py": FileType.PYTHON,
            ".js": FileType.JAVASCRIPT,
            ".ts": FileType.JAVASCRIPT,
            ".md": FileType.MARKDOWN,
            ".go": FileType.UNKNOWN,
            ".rs": FileType.UNKNOWN,
            ".ipynb": FileType.PYTHON,
        }
        return mapping.get(extension, FileType.UNKNOWN)