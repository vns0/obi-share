import aiosqlite
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timedelta
from markdown2 import markdown
from fastapi.middleware.cors import CORSMiddleware

# Инициализация приложения
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["app://obsidian.md", "http://localhost"],  # Укажите допустимые источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

# База данных SQLite
DATABASE = "notes.db"

# Модель данных для заметки
class Note(BaseModel):
    content: str
    expire_after_read: bool = True
    password: str = None


from fastapi import Header, HTTPException

# Конфигурация (замените на ваш пароль)
API_PASSWORD = "your_secure_password"

# Функция для проверки пароля
def verify_password(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    if token != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid API password")


# Создание заметки
@app.post("/create/")
async def create_note(note: Note, auth: str = Depends(verify_password)):
    note_id = str(uuid4())
    created_at = datetime.utcnow()

    # Сохранение заметки в базу данных
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            """
            INSERT INTO notes (id, content, expire_after_read, password, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (note_id, note.content, note.expire_after_read, note.password, created_at),
        )
        await db.commit()

    # Возврат ссылки на заметку
    return {"url": f"http://localhost:8000/read/{note_id}"}

import yaml
from fastapi.responses import HTMLResponse
from markdown2 import markdown

@app.get("/read/{note_id}", response_class=HTMLResponse)
async def read_note(note_id: str, password: str = None):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            "SELECT content, expire_after_read, password FROM notes WHERE id = ?",
            (note_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Note not found")

        content, expire_after_read, stored_password = row

        if stored_password and stored_password != password:
            raise HTTPException(status_code=403, detail="Invalid password")

        # Разделяем YAML и Markdown
        if content.startswith("---"):
            yaml_end_index = content.find("---", 3)  # Ищем конец YAML
            if yaml_end_index != -1:
                yaml_data = content[3:yaml_end_index].strip()
                markdown_content = content[yaml_end_index + 3:].strip()
                try:
                    parsed_yaml = yaml.safe_load(yaml_data)  # Парсим YAML
                except yaml.YAMLError as e:
                    parsed_yaml = {"error": "Failed to parse YAML", "details": str(e)}
            else:
                parsed_yaml = {}
                markdown_content = content
        else:
            parsed_yaml = {}
            markdown_content = content

        # Поддержка ссылок [[link]]
        markdown_content = markdown_content.replace("[[", "<a href='#'>").replace("]]", "</a>")

        # Рендерим Markdown в HTML
        rendered_markdown = markdown(markdown_content, extras=["fenced-code-blocks", "tables", "break-on-newline"])

        # Формируем вывод YAML как HTML
        def render_yaml(data, level=0):
            html = "<ul>"
            for key, value in data.items():
                if isinstance(value, dict):  # Если значение — вложенный словарь
                    html += f"<li><strong>{key.capitalize()}:</strong>{render_yaml(value, level + 1)}</li>"
                elif isinstance(value, list):  # Если значение — список
                    html += f"<li><strong>{key.capitalize()}:</strong><ul>"
                    for item in value:
                        html += f"<li>{item}</li>"
                    html += "</ul></li>"
                else:  # Если значение — простой текст
                    html += f"<li><strong>{key.capitalize()}:</strong> {value}</li>"
            html += "</ul>"
            return html

        yaml_html = render_yaml(parsed_yaml)

        # Удаляем запись, если требуется
        if expire_after_read:
            await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            await db.commit()

    # Формируем итоговую HTML-страницу
    return f"""
    <html>
    <head>
        <title>Shared Note</title>
        <style>
            body {{
                font-family: 'Inter', Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
            }}
            .metadata {{
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .content h1, .content h2, .content h3 {{
                margin-top: 20px;
                margin-bottom: 10px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            .content ul, .content ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}
            .content ul ul, .content ol ol {{
                margin: 5px 0;
                padding-left: 30px;
            }}
            .content li {{
                margin-bottom: 5px;
                line-height: 1.6;
            }}
            .content p {{
                margin: 10px 0;
            }}
            .content a {{
                color: #007BFF;
                text-decoration: none;
            }}
            .content a:hover {{
                text-decoration: underline;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            hr {{
                border: 0;
                border-top: 1px solid #ddd;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <h1>Shared Note</h1>
        <div class="metadata">
            {yaml_html}
        </div>
        <hr>
        <div class="content">
            {rendered_markdown}
        </div>
    </body>
    </html>
    """



# Удаление устаревших заметок
@app.delete("/cleanup/")
async def cleanup_expired_notes():
    # Удаление заметок старше 168 часов (7 дней)
    threshold = datetime.utcnow() - timedelta(hours=168)

    async with aiosqlite.connect(DATABASE) as db:
        result = await db.execute("DELETE FROM notes WHERE created_at < ?", (threshold,))
        await db.commit()

    return {"message": "Old notes cleaned up"}
