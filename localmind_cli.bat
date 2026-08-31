@echo off
echo 🧠 LocalMind CLI
echo.
set /p project_path="📂 Введите путь к папке с проектом: "
echo.
echo 🔍 Анализируем: %project_path%
echo.
localmind "%project_path%"
echo.
echo ✅ Готово! Нажми любую клавишу для выхода.
pause