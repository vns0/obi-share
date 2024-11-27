# Obsidian Note Sharing Plugin

This is a plugin for [Obsidian](https://obsidian.md) that allows you to securely share your notes with others via a unique link. Notes are served through a backend API and can include optional features like expiring after being read or requiring a password for access.

---

## **Features**
- Share notes with a unique link.
- Option to expire notes after being read.
- Password-protect your shared notes.
- Retain the original formatting of your notes, including YAML front matter and Markdown.
- View YAML metadata and Markdown content in a styled HTML page.
- Automatic cleanup of expired notes.

---

## **Setup**

### **1. Backend Requirements**

1. **Install Python and dependencies**:
   - Ensure Python 3.8+ is installed.
   - Create a virtual environment and install dependencies:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     pip install fastapi uvicorn aiosqlite markdown2 pyyaml python-dotenv
     ```

2. **Set up the SQLite database**:
   - Create the database file:
     ```bash
     touch notes.db
     ```
   - Initialize the schema:
     ```bash
     sqlite3 notes.db < schema.sql
     ```

3. **Set up environment variables**:
   - Create a `.env` file in the backend directory:
     ```plaintext
     API_PASSWORD=your_secure_password
     DATABASE_URL=notes.db
     ```

4. **Run the server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

---

### **2. Plugin Installation**

1. Clone or download this repository.
   ```bash
   git clone https://github.com/your-repo/obi-share.git
   ```
2. Place the plugin folder in your Obsidian vault under `.obsidian/plugins/obi-share`.
3. Enable the plugin in Obsidian settings.

---

## **Usage**

### **Sharing a Note**
1. Open a note in Obsidian.
2. Trigger the plugin via its command (e.g., "Share Note").
3. A modal will appear:
   - Set a password (optional).
   - Choose if the note should expire after being read.
4. Copy the generated link from the modal.

### **Accessing Shared Notes**
Recipients can view the shared note via the generated link. The note will be displayed in a styled HTML format, preserving both metadata and content.

---

## **Customization**

### **API Configuration**
- Update the backend URL in the plugin settings:
  - Default: `http://localhost:8000`

### **Frontend Styles**
- You can modify the note rendering styles in the backend's HTML template.

---

## **Endpoints**

### **`POST /create/`**
Create a new shared note.
- **Headers**: 
  - `Authorization: Bearer <API_PASSWORD>`
- **Body**:
  ```json
  {
    "content": "Your note content",
    "expire_after_read": true,
    "password": "optional_password"
  }
  ```
- **Response**:
  ```json
  {
    "url": "http://<domain>/read/<note_id>"
  }
  ```

### **`GET /read/{note_id}`**
Read a shared note.
- **Query Parameters**:
  - `password` (if required)

### **`DELETE /cleanup/`**
Clean up expired notes.
- Automatically deletes notes older than 7 days.

---

## **Known Issues**
- Ensure the backend API is running and accessible from Obsidian.
- YAML parsing errors may occur with complex metadata. Validate your YAML structure if needed.

---

## **Contributing**
Contributions are welcome! Feel free to submit pull requests or report issues in the repository.

---

## **License**
MIT License. See `LICENSE` file for details.