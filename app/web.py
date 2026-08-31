from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pathlib import Path
import tempfile
import shutil
import json
import zipfile
from datetime import datetime
import asyncio

from app.services.file_reader import FileReader
from app.services.ai_analyzer import AIAnalyzer
from app.services.mindmap_generator import MindmapGenerator
from app.services.integrity_agent import IntegrityAgent
from app.domain.schemas import ProjectMindMap
from app.core.config import settings

app = FastAPI(title="LocalMind Web", description="Веб-интерфейс для анализа кода")

UPLOAD_DIR = Path(tempfile.gettempdir()) / "localmind_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# HTML шаблон как строка (без Jinja2)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LocalMind — AI-агент для анализа кода</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 750px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-height: 95vh;
            overflow-y: auto;
        }
        h1 { color: #333; font-size: 28px; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 14px; margin-bottom: 30px; }
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-area:hover { border-color: #667eea; background: #f8f9ff; }
        .upload-area.dragover { border-color: #667eea; background: #f0f2ff; }
        .upload-icon { font-size: 48px; margin-bottom: 10px; }
        .upload-text { color: #999; font-size: 16px; }
        .upload-text strong { color: #667eea; }
        #file-input { display: none; }
        .or-divider { text-align: center; color: #999; margin: 20px 0; font-size: 14px; }
        .path-input-group {
            display: flex;
            gap: 10px;
        }
        .path-input-group input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .path-input-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            color: white;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-success {
            background: #4CAF50;
        }
        .btn-success:hover { background: #45a049; }
        .btn-danger {
            background: #dc3545;
        }
        .btn-danger:hover { background: #c82333; }
        .btn-warning {
            background: #ffc107;
            color: #333;
        }
        .btn-warning:hover { background: #e0a800; }
        #result { margin-top: 30px; display: none; }
        .result-card { background: #f8f9fa; border-radius: 12px; padding: 20px; }
        .result-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        .stat-item {
            background: white;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .stat-number { font-size: 24px; font-weight: 700; color: #333; }
        .stat-label { font-size: 12px; color: #999; margin-top: 5px; }
        .result-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            vertical-align: middle;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .status-text { display: inline-block; vertical-align: middle; }
        .extensions-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        .extension-tag {
            background: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            border: 1px solid #e0e0e0;
        }
        #progress { margin-top: 20px; display: none; }
        
        /* Integrity styles */
        #integrity-container {
            margin-top: 20px;
            display: none;
        }
        #integrity-status {
            padding: 15px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            text-align: center;
        }
        .integrity-file-item {
            padding: 10px;
            margin: 5px 0;
            background: #f5f5f5;
            border-radius: 4px;
            border-left: 4px solid #999;
        }
        .integrity-file-item.error { border-left-color: #c62828; }
        .integrity-file-item.warning { border-left-color: #e65100; }
        .integrity-file-item.green { border-left-color: #1b5e20; }
        .integrity-error { color: #c62828; font-size: 12px; margin-top: 5px; }
        .integrity-warning { color: #e65100; font-size: 12px; margin-top: 5px; }
        .integrity-info { color: #0d47a1; font-size: 12px; margin-top: 5px; }
        
        /* Scrollable details */
        #integrity-details {
            max-height: 300px;
            overflow-y: auto;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 LocalMind</h1>
        <div class="subtitle">AI-агент для анализа кода и генерации интерактивных mindmap</div>
        
        <div class="upload-area" id="upload-area">
            <div class="upload-icon">📁</div>
            <div class="upload-text">
                <strong>Нажмите</strong> или перетащите ZIP-архив с проектом
            </div>
            <input type="file" id="file-input" accept=".zip">
        </div>
        
        <div class="or-divider">— или —</div>
        
        <div class="path-input-group">
            <input type="text" id="path-input" placeholder="Введите путь к папке с проектом">
            <button class="btn btn-primary" id="analyze-path-btn">Анализировать</button>
        </div>
        
        <div id="progress">
            <div class="loader"></div>
            <span class="status-text" id="status-text">Анализируем проект...</span>
        </div>
        
        <div id="result">
            <div class="result-card">
                <h3 id="result-title" style="margin-bottom: 15px;">📊 Результат</h3>
                <div class="result-stats" id="result-stats"></div>
                <div id="extensions-container"></div>
                <div id="summary-container" style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px;">
                    <p id="summary-text" style="color: #555; font-size: 14px; line-height: 1.6;"></p>
                </div>
                
                <!-- Integrity Block -->
                <div id="integrity-container">
                    <h3 style="margin-top: 15px;">🔒 Целостность кода</h3>
                    <div id="integrity-status"></div>
                    <div id="integrity-details"></div>
                </div>
                
                <div class="result-actions">
                    <button class="btn btn-success" id="view-html-btn">👁️ Просмотреть карту</button>
                    <button class="btn btn-primary" id="download-html-btn">⬇️ Скачать HTML</button>
                    <button class="btn btn-danger" id="download-pdf-btn">⬇️ Скачать PDF</button>
                    <button class="btn btn-warning" id="ai-analyze-btn" style="display: none;">🧠 AI-анализ</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentProject = null;
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const pathInput = document.getElementById('path-input');
        const analyzePathBtn = document.getElementById('analyze-path-btn');
        const progress = document.getElementById('progress');
        const statusText = document.getElementById('status-text');
        const result = document.getElementById('result');
        const resultStats = document.getElementById('result-stats');
        const extensionsContainer = document.getElementById('extensions-container');
        const summaryText = document.getElementById('summary-text');
        const resultTitle = document.getElementById('result-title');
        const integrityContainer = document.getElementById('integrity-container');
        const integrityStatus = document.getElementById('integrity-status');
        const integrityDetails = document.getElementById('integrity-details');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleUpload();
            }
        });
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleUpload);

        analyzePathBtn.addEventListener('click', () => {
            const path = pathInput.value.trim();
            if (!path) {
                alert('Введите путь к папке');
                return;
            }
            analyzeProject(path);
        });

        async function handleUpload() {
            if (!fileInput.files.length) return;
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('project_name', file.name.replace('.zip', ''));
            await sendRequest('/upload', formData);
        }

        async function analyzeProject(path) {
            console.log("🔍 Анализируем путь:", path);
            const formData = new FormData();
            formData.append('path', path);
            const name = path.replace(/\\\\/g, '/').split('/').pop() || 'project';
            formData.append('name', name);
            console.log("📤 Отправляем запрос...");
            await sendRequest('/analyze-path', formData);
        }

        async function sendRequest(url, formData) {
            console.log("📡 Отправка запроса на:", url);
            progress.style.display = 'block';
            result.style.display = 'none';
            integrityContainer.style.display = 'none';
            statusText.textContent = 'Анализируем проект...';

            try {
                const response = await fetch(url, { method: 'POST', body: formData });
                console.log("📥 Ответ получен, статус:", response.status);
                const data = await response.json();
                console.log("📦 Данные:", data);

                if (data.success) {
                    currentProject = data.project_name;
                    showResult(data);
                } else {
                    alert('Ошибка: ' + (data.detail || 'Неизвестная ошибка'));
                }
            } catch (err) {
                console.error("❌ Ошибка:", err);
                alert('Ошибка: ' + err.message);
            } finally {
                progress.style.display = 'none';
            }
        }

        function showResult(data) {
            result.style.display = 'block';
            resultTitle.textContent = '📊 ' + data.project_name;

            resultStats.innerHTML = `
                <div class="stat-item"><div class="stat-number">${data.total_files}</div><div class="stat-label">📁 Файлов</div></div>
                <div class="stat-item"><div class="stat-number">${data.total_lines}</div><div class="stat-label">📝 Строк</div></div>
                <div class="stat-item"><div class="stat-number">${data.total_entities}</div><div class="stat-label">🏷️ Сущностей</div></div>
            `;

            if (data.extensions) {
                let html = '<div class="extensions-list">';
                for (const [ext, count] of Object.entries(data.extensions)) {
                    html += `<span class="extension-tag">${ext}: ${count}</span>`;
                }
                html += '</div>';
                extensionsContainer.innerHTML = html;
            } else {
                extensionsContainer.innerHTML = '';
            }

            summaryText.textContent = data.summary || 'Описание не сгенерировано';

            // === Integrity ===
            if (data.integrity) {
                integrityContainer.style.display = 'block';
                const status = data.integrity;
                
                // Status badge
                let statusText = status.status_icon + ' ' + status.overall_status.toUpperCase();
                let bgColor = status.overall_status === 'red' ? '#ffebee' :
                              status.overall_status === 'yellow' ? '#fff3e0' : '#e8f5e9';
                let textColor = status.overall_status === 'red' ? '#c62828' :
                                status.overall_status === 'yellow' ? '#e65100' : '#1b5e20';
                
                integrityStatus.textContent = statusText;
                integrityStatus.style.background = bgColor;
                integrityStatus.style.color = textColor;
                
                // Details
                let detailsHtml = `<div style="margin-top: 10px;">
                    <p>📊 Всего файлов: ${status.total_files}</p>
                    <p>❌ Ошибок: ${status.total_errors} | ⚠️ Предупреждений: ${status.total_warnings}</p>
                    <p style="font-weight: 500;">${status.summary}</p>
                </div>`;
                
                // File list
                if (status.results && status.results.length > 0) {
                    detailsHtml += `<div style="margin-top: 10px; max-height: 300px; overflow-y: auto;">`;
                    for (const fileResult of status.results) {
                        if (fileResult.errors.length > 0 || fileResult.warnings.length > 0) {
                            let borderColor = fileResult.errors.length > 0 ? '#c62828' : '#e65100';
                            let icon = fileResult.errors.length > 0 ? '🔴' : '🟡';
                            detailsHtml += `<div style="padding: 10px; margin: 5px 0; background: #fafafa; border-radius: 4px; border-left: 4px solid ${borderColor};">
                                <strong>${icon} ${fileResult.file_path}</strong>
                                ${fileResult.errors.length > 0 ? `<div style="color: #c62828; font-size: 12px; margin-top: 5px;">❌ ${fileResult.errors.length} ошибок</div>` : ''}
                                ${fileResult.warnings.length > 0 ? `<div style="color: #e65100; font-size: 12px; margin-top: 5px;">⚠️ ${fileResult.warnings.length} предупреждений</div>` : ''}
                                ${fileResult.errors.length > 0 ? fileResult.errors.map(e => `<div class="integrity-error">• ${e.message}</div>`).join('') : ''}
                                ${fileResult.warnings.length > 0 ? fileResult.warnings.map(w => `<div class="integrity-warning">• ${w.message}</div>`).join('') : ''}
                                ${fileResult.info && fileResult.info.length > 0 ? fileResult.info.map(i => `<div class="integrity-info">• ${i.message}</div>`).join('') : ''}
                            </div>`;
                        }
                    }
                    detailsHtml += `</div>`;
                }
                
                integrityDetails.innerHTML = detailsHtml;
            }

            // Buttons
            document.getElementById('view-html-btn').onclick = () => {
                window.open(`/view/${data.project_name}`, '_blank');
            };
            document.getElementById('download-html-btn').onclick = () => {
                window.open(`/download/${data.project_name}?format=html`, '_blank');
            };
            document.getElementById('download-pdf-btn').onclick = () => {
                window.open(`/download-pdf/${data.project_name}`, '_blank');
            };
        }
    </script>
</body>
</html>
"""

# ========== Эндпоинты ==========

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница"""
    return INDEX_HTML

@app.post("/upload")
async def upload_project(
    file: UploadFile = File(...),
    project_name: str = Form("uploaded_project")
):
    """Загружает ZIP-архив с проектом и анализирует его"""
    temp_zip = UPLOAD_DIR / file.filename
    with open(temp_zip, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    extract_dir = UPLOAD_DIR / project_name
    extract_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    result = await analyze_project_dir(str(extract_dir), project_name)
    return JSONResponse(result)

@app.post("/analyze-path")
async def analyze_path(
    path: str = Form(...),
    name: str = Form("project")
):
    """Анализирует папку по указанному пути"""
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail=f"Папка {path} не найдена")
    
    result = await analyze_project_dir(path, name)
    return JSONResponse(result)

async def analyze_project_dir(path: str, project_name: str) -> dict:
    """Анализирует папку и возвращает результат в JSON"""
    reader = FileReader()
    analyzer = AIAnalyzer()
    integrity_agent = IntegrityAgent()
    all_entities = []
    total_files = 0
    total_lines = 0
    all_files = []  # Для проверки целостности
    
    async for file_info in reader.scan_directory(path, settings.ALLOWED_EXTENSIONS):
        total_files += 1
        total_lines += len(file_info.content.splitlines())
        entities = await analyzer.extract_entities(file_info.content, file_info.file_type.value)
        all_entities.extend(entities)
        all_files.append({
            "path": file_info.path,
            "content": file_info.content,
            "type": file_info.file_type.value
        })
    
    stats = reader.get_total_stats()
    summary = await analyzer.generate_summary(all_entities)
    
    # Проверка целостности
    integrity_result = await integrity_agent.check_all_files(all_files)
    
    mindmap = ProjectMindMap(
        project_name=project_name,
        total_files=total_files,
        total_lines=total_lines,
        entities=all_entities,
        connections=[],
        summary=summary,
        generated_at=datetime.now()
    )
    
    generator = MindmapGenerator()
    html_content = await generator.render_html(mindmap)
    
    html_path = UPLOAD_DIR / f"{project_name}_mindmap.html"
    html_path.write_text(html_content, encoding="utf-8")
    
    data_path = UPLOAD_DIR / f"{project_name}_data.json"
    data_path.write_text(
        json.dumps({
            "entities": [e.dict() for e in all_entities],
            "stats": stats,
            "summary": summary,
            "project_name": project_name,
            "total_files": total_files,
            "total_lines": total_lines,
            "generated_at": mindmap.generated_at.isoformat(),
            "integrity": integrity_result
        }, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )
    
    return {
        "success": True,
        "project_name": project_name,
        "total_files": total_files,
        "total_lines": total_lines,
        "total_entities": len(all_entities),
        "html_path": str(html_path),
        "data_path": str(data_path),
        "summary": summary,
        "extensions": stats.get("extensions", {}),
        "integrity": integrity_result
    }

@app.get("/download/{project_name}")
async def download_result(project_name: str, format: str = "html"):
    """Скачивает результат в формате HTML"""
    if format == "html":
        file_path = UPLOAD_DIR / f"{project_name}_mindmap.html"
    else:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(file_path, filename=file_path.name)

@app.get("/view/{project_name}")
async def view_result(project_name: str):
    """Показывает HTML-карту в браузере"""
    html_path = UPLOAD_DIR / f"{project_name}_mindmap.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="HTML не найден")
    return FileResponse(html_path)

@app.get("/download-pdf/{project_name}")
async def download_pdf(project_name: str):
    """Генерирует и скачивает PDF-отчёт"""
    data_path = UPLOAD_DIR / f"{project_name}_data.json"
    if not data_path.exists():
        raise HTTPException(status_code=404, detail="Данные не найдены")
    
    # Простая генерация PDF через отчет
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        pdf_path = UPLOAD_DIR / f"{project_name}_report.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        story.append(Paragraph(f"Отчет по проекту: {data.get('project_name', 'Unknown')}", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Файлов: {data.get('total_files', 0)}", styles['Normal']))
        story.append(Paragraph(f"Строк: {data.get('total_lines', 0)}", styles['Normal']))
        story.append(Paragraph(f"Сущностей: {len(data.get('entities', []))}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(data.get('summary', 'Нет описания'), styles['Normal']))
        
        doc.build(story)
        return FileResponse(pdf_path, filename=f"{project_name}_report.pdf")
    except ImportError:
        return JSONResponse({"error": "PDF generation requires reportlab. Install: pip install reportlab"})
    except Exception as e:
        return JSONResponse({"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)