@echo off
echo 🧠 Запуск LocalMind...
echo.
echo 🌐 Открываю веб-интерфейс...
start http://127.0.0.1:8000
echo.
echo ⏳ Ожидаем запуска сервера...
timeout /t 3 /nobreak > nul
echo.
echo 🚀 Сервер запущен! Нажми Ctrl+C для остановки.
echo.
python -m app.web
pause