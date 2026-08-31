import sys
import asyncio
import argparse
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from app.services.file_reader import FileReader
from app.services.ai_analyzer import AIAnalyzer
from app.services.mindmap_generator import MindmapGenerator
from app.domain.schemas import ProjectMindMap
from app.core.config import settings
from datetime import datetime

console = Console()

async def analyze_project(path: str, output: str, max_files: int = 0):
    """Анализирует проект и генерирует mindmap"""
    
    console.print(f"\n[bold cyan]🧠 LocalMind AI-Agent[/bold cyan]")
    console.print(f"[dim]Анализ папки: {path}[/dim]")
    console.print(f"[dim]Максимум файлов: {max_files if max_files > 0 else 'без ограничений'}[/dim]\n")
    
    reader = FileReader()
    analyzer = AIAnalyzer()
    all_entities = []
    total_files = 0
    total_lines = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Сканирование файлов...", total=None)
        
        async for file_info in reader.scan_directory(path, settings.ALLOWED_EXTENSIONS):
            if max_files > 0 and total_files >= max_files:
                break
                
            total_files += 1
            total_lines += len(file_info.content.splitlines())
            entities = await analyzer.extract_entities(file_info.content, file_info.file_type.value)
            all_entities.extend(entities)
            
            progress.update(
                task, 
                description=f"[green]Обработано: {total_files} файлов, найдено {len(all_entities)} сущностей"
            )
    
    # 👇 НОВОЕ: показываем статистику расширений
    console.print(f"\n[bold green]✅ Сканирование завершено![/bold green]")
    stats = reader.get_total_stats()
    console.print(f"[dim]📁 Файлов: {stats['total_files']} | 📝 Строк: {total_lines} | 🏷️ Сущностей: {len(all_entities)}[/dim]")
    
    if stats.get("extensions"):
        console.print("[dim]📊 Расширения файлов:[/dim]")
        for ext, count in sorted(stats["extensions"].items(), key=lambda x: x[1], reverse=True):
            console.print(f"[dim]  {ext}: {count} файлов[/dim]")
    console.print()
    
    # Генерируем summary
    console.print("[yellow]⏳ Генерация описания проекта...[/yellow]")
    summary = await analyzer.generate_summary(all_entities)
    
    # Создаём MindMap
    mindmap = ProjectMindMap(
        project_name=Path(path).name,
        total_files=total_files,
        total_lines=total_lines,
        entities=all_entities,
        connections=[],
        summary=summary,
        generated_at=datetime.now()
    )
    
    # Генерируем HTML
    console.print("[yellow]⏳ Генерация HTML-карты...[/yellow]")
    generator = MindmapGenerator()
    html = await generator.render_html(mindmap)
    await generator.save_to_file(html, output)
    
    console.print(f"\n[bold green]🎉 Готово![/bold green]")
    console.print(f"[cyan]📄 Карта сохранена в: {output}[/cyan]")
    console.print(f"[dim]Открой файл в браузере, чтобы увидеть результат[/dim]\n")

def main():
    parser = argparse.ArgumentParser(
        description="LocalMind — AI-агент для анализа кода и генерации mindmap",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  localmind ./my_project
  localmind ./my_project --output map.html
  localmind ./my_project --max-files 50
        """
    )
    
    parser.add_argument(
        "path",
        help="Путь к папке с проектом для анализа"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="mindmap.html",
        help="Путь для сохранения HTML-карты (по умолчанию: mindmap.html)"
    )
    
    parser.add_argument(
        "-m", "--max-files",
        type=int,
        default=0,
        help="Максимальное количество файлов для анализа (0 = без ограничений)"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="LocalMind v0.1.0"
    )
    
    args = parser.parse_args()
    
    # Проверяем, что путь существует
    if not Path(args.path).exists():
        console.print(f"[bold red]❌ Ошибка: Папка '{args.path}' не найдена[/bold red]")
        sys.exit(1)
    
    try:
        asyncio.run(analyze_project(args.path, args.output, args.max_files))
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Прервано пользователем[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]❌ Ошибка: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()