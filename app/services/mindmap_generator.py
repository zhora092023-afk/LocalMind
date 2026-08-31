import json
from typing import List, Dict
from pathlib import Path
from app.interfaces import IMindmapGenerator
from app.domain.schemas import ProjectMindMap

class MindmapGenerator(IMindmapGenerator):
    """Генерирует интерактивную HTML-карту проекта"""
    
    async def render_html(self, mindmap: ProjectMindMap) -> str:
        """Создаёт HTML-страницу с визуализацией"""
        
        # Подготавливаем данные
        nodes = []
        links = []
        
        # Создаём узлы для каждой сущности
        for idx, entity in enumerate(mindmap.entities):
            color = self._get_color_by_type(entity.entity_type)
            nodes.append({
                "id": idx,
                "label": entity.name[:30],  # Обрезаем длинные имена
                "type": entity.entity_type,
                "color": color,
                "size": 15 if entity.entity_type == "class" else 10,
                "title": entity.description[:50]  # Подсказка при наведении
            })
        
        # Если связей нет — создаём простую цепочку, чтобы граф не был пустым
        if not links and len(nodes) > 1:
            for i in range(len(nodes) - 1):
                links.append({
                    "from": i,
                    "to": i + 1,
                    "label": "связь"
                })
        
        # Генерируем HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mindmap: {mindmap.project_name}</title>
    <script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
        }}
        #header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        #header h1 {{ margin: 0; font-size: 24px; }}
        #header .stats {{
            margin-top: 5px;
            font-size: 14px;
            opacity: 0.9;
        }}
        #container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        #mynetwork {{
            width: 100%;
            height: 800px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .legend {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
        }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 5px;
            vertical-align: middle;
        }}
        .summary-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        .summary-box h3 {{ margin-top: 0; }}
        .summary-box pre {{
            white-space: pre-wrap;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            line-height: 1.6;
        }}
        .footer {{
            color: #666;
            font-size: 12px;
            text-align: center;
            margin-top: 20px;
            padding: 10px;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🧠 Проект: {mindmap.project_name}</h1>
        <div class="stats">
            📁 {mindmap.total_files} файлов | 
            📝 {mindmap.total_lines} строк | 
            🏷️ {len(mindmap.entities)} сущностей
        </div>
    </div>
    
    <div id="container">
        <div class="legend">
            <span class="legend-item">
                <span class="legend-color" style="background:#4CAF50;"></span> Классы
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background:#FF9800;"></span> Функции
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background:#2196F3;"></span> Импорты
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background:#9C27B0;"></span> Другое
            </span>
        </div>
        
        <div id="mynetwork"></div>
        
        <div class="summary-box">
            <h3>📊 Краткое описание</h3>
            <pre>{mindmap.summary}</pre>
            <p style="color: #666; font-size: 12px; margin-top: 10px;">
                Сгенерировано: {mindmap.generated_at.strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </div>
        
        <div class="footer">
            Сгенерировано с помощью LocalMind AI-Agent
        </div>
    </div>
    
    <script>
        (function() {{
            console.log("🚀 Запуск визуализации...");
            console.log("Узлов:", {len(nodes)});
            console.log("Связей:", {len(links)});
            
            const nodesData = {json.dumps(nodes)};
            const edgesData = {json.dumps(links)};
            
            // Создаём контейнер
            const container = document.getElementById('mynetwork');
            if (!container) {{
                console.error("❌ Контейнер не найден!");
                return;
            }}
            
            // Преобразуем данные
            const nodes = new vis.DataSet(nodesData.map(n => ({{
                id: n.id,
                label: n.label,
                color: n.color,
                size: n.size,
                title: n.title || n.label,
                shape: 'dot'
            }})));
            
            const edges = new vis.DataSet(edgesData.map(e => ({{
                from: e.from,
                to: e.to,
                label: e.label || '',
                arrows: 'to',
                color: {{ color: '#848484' }}
            }})));
            
            // Настройки графа
            const options = {{
                nodes: {{
                    shape: 'dot',
                    size: 15,
                    font: {{
                        size: 14,
                        face: 'Segoe UI'
                    }}
                }},
                edges: {{
                    arrows: {{
                        to: {{ enabled: true, scaleFactor: 0.5 }}
                    }},
                    color: {{ color: '#848484' }},
                    smooth: {{
                        enabled: true,
                        type: 'dynamic'
                    }}
                }},
                physics: {{
                    enabled: true,
                    stabilization: {{
                        iterations: 200,
                        updateInterval: 25
                    }},
                    barnesHut: {{
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 95,
                        springConstant: 0.04,
                        damping: 0.09,
                        avoidOverlap: 0.1
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 200,
                    zoomView: true,
                    dragView: true
                }}
            }};
            
            try {{
                const network = new vis.Network(container, {{ nodes, edges }}, options);
                console.log("✅ Граф успешно создан!");
                
                // Событие после стабилизации
                network.once('stabilizationIterationsDone', function() {{
                    console.log("🎯 Стабилизация завершена!");
                    network.fit();
                }});
                
                // Обработка ошибок
                network.on('error', function(err) {{
                    console.error("❌ Ошибка сети:", err);
                }});
                
            }} catch (err) {{
                console.error("❌ Ошибка при создании графа:", err);
                document.getElementById('mynetwork').innerHTML = 
                    '<div style="padding: 40px; text-align: center; color: red;">' +
                    '⚠️ Ошибка при создании графа. Проверьте консоль разработчика (F12).' +
                    '</div>';
            }}
        }})();
    </script>
</body>
</html>
"""
        return html
    
    async def save_to_file(self, html_content: str, output_path: str) -> None:
        """Сохраняет HTML на диск"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html_content, encoding='utf-8')
    
    def _get_color_by_type(self, entity_type: str) -> str:
        """Определяет цвет для типа сущности"""
        colors = {
            "class": "#4CAF50",
            "function": "#FF9800",
            "import": "#2196F3",
        }
        return colors.get(entity_type, "#9C27B0")