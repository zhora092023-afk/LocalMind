# Файл app/main.py (Точка входа — заглушка для архитектуры)

import asyncio
from rich.console import Console
from app.core.config import settings
from app.interfaces import IFileReader, IAnalyzer, IMindmapGenerator

console = Console()

async def main() -> None:
    console.print("[bold cyan]🧠 LocalMind AI-Agent[/bold cyan]")
    console.print(f"[dim]Анализ папки: {settings.PROJECT_PATH}[/dim]")
    
    # TODO: Здесь будет внедрение зависимостей (Dependency Injection)
    # Пока просто заглушка, чтобы структура проходила проверку
    
    console.print("[yellow]⏳ Ожидаем реализации от агентов...[/yellow]")

if __name__ == "__main__":
    asyncio.run(main())