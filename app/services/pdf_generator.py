from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from pathlib import Path
import json
from datetime import datetime

class PDFGenerator:
    @staticmethod
    async def generate_report(data_path: str, output_path: str):
        """Генерирует PDF-отчёт на основе данных анализа"""
        
        # Загружаем данные
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30
        )
        
        story = []
        
        # Заголовок
        story.append(Paragraph(f"🧠 Анализ проекта: {data['project_name']}", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Статистика
        stats = data.get('stats', {})
        story.append(Paragraph("📊 Статистика", styles['Heading2']))
        story.append(Paragraph(f"📁 Файлов: {data['total_files']}", styles['Normal']))
        story.append(Paragraph(f"📝 Строк: {data['total_lines']}", styles['Normal']))
        story.append(Paragraph(f"🏷️ Сущностей: {data['total_entities']}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Расширения
        if stats.get('extensions'):
            story.append(Paragraph("📂 Расширения файлов:", styles['Heading2']))
            for ext, count in stats['extensions'].items():
                story.append(Paragraph(f"  {ext}: {count} файлов", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Summary
        story.append(Paragraph("📝 Описание проекта", styles['Heading2']))
        story.append(Paragraph(data.get('summary', 'Нет описания'), styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Сущности (первые 20)
        entities = data.get('entities', [])[:20]
        if entities:
            story.append(Paragraph("🏷️ Основные сущности", styles['Heading2']))
            table_data = [["Тип", "Имя", "Описание"]]
            for e in entities:
                table_data.append([
                    e.get('entity_type', 'unknown'),
                    e.get('name', '')[:30],
                    e.get('description', '')[:50]
                ])
            
            table = Table(table_data, colWidths=[1.2*inch, 2*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(table)
        
        # Дата генерации
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles['Normal']
        ))
        
        doc.build(story)