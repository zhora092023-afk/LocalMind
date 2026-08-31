import ast
import re
import json
from typing import List, Dict, Set, Tuple, Any
from pathlib import Path

class IntegrityStatus:
    """Статус целостности кода"""
    GREEN = "🟢"
    YELLOW = "🟡"
    RED = "🔴"
    
    @staticmethod
    def get_status_color(status: str) -> str:
        colors = {
            "green": "🟢",
            "yellow": "🟡",
            "red": "🔴"
        }
        return colors.get(status, "⚪")

class IntegrityAgent:
    """Агент проверки целостности кода"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.is_ipynb = False
        self._current_file = ""
        self._cell_info = []  # Хранит информацию о ячейках: (start_line, cell_index, lines)
        
    async def check_integrity(self, file_path: str, content: str, file_type: str) -> Dict[str, Any]:
        """Проверяет целостность одного файла"""
        
        self.errors = []
        self.warnings = []
        self.info = []
        self.is_ipynb = False
        self._current_file = file_path
        self._cell_info = []
        
        # Проверяем, является ли файл Jupyter Notebook
        if file_path.endswith('.ipynb') or '.ipynb' in file_path:
            self.is_ipynb = True
        
        # Пропускаем checkpoint-файлы
        if '.ipynb_checkpoints' in file_path:
            self.info.append({
                "type": "Skipped",
                "message": f"ℹ️ Файл {Path(file_path).name}: пропущен (автосохранение Jupyter)",
                "file": Path(file_path).name
            })
            return self._build_result(file_path)
        
        # Для Jupyter Notebook извлекаем код из ячеек с информацией о номерах
        if self.is_ipynb:
            try:
                data = json.loads(content)
                code_parts = []
                self._cell_info = []
                line_counter = 0
                cell_counter = 0
                
                for cell in data.get("cells", []):
                    if cell.get("cell_type") == "code":
                        cell_counter += 1
                        source = cell.get("source", [])
                        cell_lines = []
                        if isinstance(source, list):
                            for line in source:
                                code_parts.append(line)
                                cell_lines.append(line)
                                line_counter += 1
                        else:
                            code_parts.append(str(source))
                            cell_lines.append(str(source))
                            line_counter += 1
                        
                        # Сохраняем информацию о ячейке
                        self._cell_info.append({
                            "cell_index": cell_counter,
                            "start_line": line_counter - len(cell_lines),
                            "end_line": line_counter,
                            "lines": cell_lines
                        })
                
                content = "".join(code_parts)
            except:
                pass
        
        if file_type == "python" or self.is_ipynb:
            self._check_python_integrity(content, file_path)
        elif file_type in ["javascript", "typescript"]:
            self._check_js_integrity(content, file_path)
        else:
            self.info.append({
                "type": "Unsupported",
                "message": f"ℹ️ Файл {Path(file_path).name}: проверка не поддерживается",
                "file": Path(file_path).name
            })
        
        return self._build_result(file_path)
    
    def _get_cell_info(self, global_line: int) -> Dict[str, Any]:
        """Возвращает информацию о ячейке по глобальному номеру строки"""
        if not self.is_ipynb or not self._cell_info:
            return {"cell_index": None, "local_line": global_line}
        
        for cell in self._cell_info:
            if cell["start_line"] <= global_line <= cell["end_line"]:
                local_line = global_line - cell["start_line"]
                return {
                    "cell_index": cell["cell_index"],
                    "local_line": local_line,
                    "line_content": cell["lines"][local_line - 1] if 0 <= local_line - 1 < len(cell["lines"]) else ""
                }
        
        return {"cell_index": None, "local_line": global_line}
    
    def _build_result(self, file_path: str) -> Dict[str, Any]:
        """Собирает результат проверки"""
        status = self._determine_status()
        return {
            "file_path": file_path,
            "status": status,
            "status_icon": IntegrityStatus.get_status_color(status),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "is_ipynb": self.is_ipynb,
            "is_checkpoint": '.ipynb_checkpoints' in file_path
        }
    
    def _determine_status(self) -> str:
        """Определяет общий статус на основе ошибок и предупреждений"""
        if self.errors:
            return "red"
        elif self.warnings and not self.is_ipynb:
            return "yellow"
        else:
            return "green"
    
    def _check_python_integrity(self, content: str, file_path: str):
        """Проверка целостности Python-файла"""
        
        # 1. Проверка синтаксиса (критическая ошибка)
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # Получаем информацию о строке
            global_line = e.lineno if e.lineno else 0
            cell_info = self._get_cell_info(global_line)
            
            if self.is_ipynb:
                msg = f"⚠️ Синтаксическая ошибка"
                if cell_info.get("cell_index"):
                    msg += f" в ячейке {cell_info['cell_index']}"
                if cell_info.get("local_line"):
                    msg += f", строка {cell_info['local_line']}"
                msg += f": {e.msg}"
                
                if cell_info.get("line_content"):
                    msg += f"\n   Содержимое: {cell_info['line_content'][:100]}"
                
                self.warnings.append({
                    "type": "SyntaxWarning",
                    "message": msg,
                    "file": Path(file_path).name,
                    "cell": cell_info.get("cell_index"),
                    "line": cell_info.get("local_line"),
                    "suggestion": "Проверьте код на наличие нестандартных символов (длинное тире, эмодзи, кавычки-ёлочки)"
                })
                return
            else:
                self.errors.append({
                    "type": "SyntaxError",
                    "message": f"Ошибка синтаксиса в строке {global_line}: {e.msg}",
                    "line": global_line,
                    "file": Path(file_path).name
                })
                return
        except Exception as e:
            self.errors.append({
                "type": "ParseError",
                "message": f"Ошибка парсинга: {str(e)}",
                "file": Path(file_path).name
            })
            return
        
        # Для Jupyter Notebook пропускаем остальные проверки
        if self.is_ipynb:
            return
        
        # 2. Проверка импортов (только для обычных .py файлов)
        imports = self._extract_imports(tree)
        used_names = self._extract_used_names(tree)
        
        unused_imports = []
        for imp in imports:
            if imp not in used_names and imp not in ["os", "sys", "re"]:
                unused_imports.append(imp)
        
        if unused_imports:
            self.warnings.append({
                "type": "UnusedImport",
                "message": f"⚠️ Неиспользуемые импорты: {', '.join(unused_imports[:5])}",
                "file": Path(file_path).name,
                "suggestion": "Удалите неиспользуемые импорты или используйте их в коде"
            })
        
        # 3. Проверка длины функций
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        long_functions = []
        for func in functions:
            line_count = func.end_lineno - func.lineno + 1 if func.end_lineno else 0
            if line_count > 50:
                long_functions.append((func.name, line_count))
        
        if long_functions:
            for name, lines in long_functions[:3]:
                self.warnings.append({
                    "type": "LongFunction",
                    "message": f"⚠️ Функция '{name}' слишком длинная ({lines} строк). Рекомендуется разбить на части",
                    "file": Path(file_path).name,
                    "suggestion": f"Разбейте функцию '{name}' на более мелкие функции (максимум 30 строк)"
                })
        
        # 4. Проверка на дублирование кода
        duplicates = self._find_duplicates(tree)
        if duplicates:
            for dup in duplicates[:3]:
                self.warnings.append({
                    "type": "CodeDuplication",
                    "message": f"⚠️ Обнаружено дублирование кода: '{dup[:30]}...'",
                    "file": Path(file_path).name,
                    "suggestion": "Вынесите повторяющийся код в отдельную функцию"
                })
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Извлекает все импорты из AST"""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports
    
    def _extract_used_names(self, tree: ast.AST) -> Set[str]:
        """Извлекает все используемые имена из AST"""
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used.add(node.value.id)
        return used
    
    def _find_duplicates(self, tree: ast.AST) -> List[str]:
        """Находит дублирующиеся строки кода (упрощённо)"""
        try:
            lines = ast.unparse(tree).split('\n')
        except:
            return []
        
        duplicates = []
        seen = set()
        for line in lines:
            line = line.strip()
            if len(line) > 30 and line in seen:
                duplicates.append(line[:50])
            else:
                seen.add(line)
        return list(set(duplicates))[:5]
    
    def _check_js_integrity(self, content: str, file_path: str):
        """Базовая проверка JavaScript/TypeScript файлов"""
        
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            self.errors.append({
                "type": "SyntaxError",
                "message": f"Несоответствие скобок: открывающих {open_braces}, закрывающих {close_braces}",
                "file": Path(file_path).name
            })
    
    async def check_all_files(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Проверяет целостность всех файлов в проекте"""
        
        results = []
        total_errors = 0
        total_warnings = 0
        statuses = []
        skipped_count = 0
        
        for file_info in files:
            result = await self.check_integrity(
                file_info.get("path", ""),
                file_info.get("content", ""),
                file_info.get("type", "")
            )
            results.append(result)
            
            if result.get('is_checkpoint', False):
                skipped_count += 1
                continue
            
            total_errors += result["error_count"]
            total_warnings += result["warning_count"]
            statuses.append(result["status"])
        
        if "red" in statuses:
            overall_status = "red"
        elif "yellow" in statuses:
            overall_status = "yellow"
        else:
            overall_status = "green"
        
        return {
            "overall_status": overall_status,
            "status_icon": IntegrityStatus.get_status_color(overall_status),
            "total_files": len(results),
            "skipped_checkpoints": skipped_count,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "results": results,
            "summary": self._generate_summary(results, overall_status, skipped_count)
        }
    
    def _generate_summary(self, results: List[Dict], overall_status: str, skipped: int = 0) -> str:
        """Генерирует текстовое описание статуса"""
        
        skip_note = f" (пропущено {skipped} checkpoint-файлов)" if skipped > 0 else ""
        
        if overall_status == "red":
            return f"🔴 КРИТИЧЕСКАЯ ОШИБКА! Целостность кода нарушена! Обнаружены синтаксические ошибки, которые препятствуют выполнению кода. Немедленно устраните ошибки.{skip_note}"
        elif overall_status == "yellow":
            return f"🟡 НЕСТАБИЛЬНАЯ РАБОТА. Обнаружены проблемы с качеством кода: неиспользуемые импорты, длинные функции, дублирование. Рекомендуется рефакторинг.{skip_note}"
        else:
            return f"🟢 ФУНКЦИОНАЛ РАБОТАЕТ ШТАТНО! Код чистый, структурированный, соответствует лучшим практикам.{skip_note}"