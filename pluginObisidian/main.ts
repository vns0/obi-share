import { Plugin, PluginSettingTab, App, Setting, Notice, Modal } from "obsidian";



interface ShareNoteSettings {
    apiBaseUrl: string; // URL API
    apiPassword: string; // Пароль для API
}

const DEFAULT_SETTINGS: ShareNoteSettings = {
    apiBaseUrl: "http://localhost:8000", // Значение по умолчанию
    apiPassword: "", // Пустой пароль по умолчанию
};

// Основной плагин
export default class ShareNotePlugin extends Plugin {
    settings: ShareNoteSettings;

    async onload() {
        await this.loadSettings();

        // Добавляем команду для публикации заметки
        this.addCommand({
            id: "share-current-note",
            name: "Share Current Note",
            callback: async () => {
                const activeFile = this.app.workspace.getActiveFile();
                if (!activeFile) {
                    new Notice("No active note to share!");
                    return;
                }

                const content = await this.app.vault.read(activeFile);

                // Открываем модальное окно
                new ShareNoteModal(this.app, this.settings, content).open();
            },
        });

        // Добавляем вкладку настроек
        this.addSettingTab(new ShareNoteSettingTab(this.app, this));
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }
}

// Модальное окно для публикации заметки
class ShareNoteModal extends Modal {
  private apiBaseUrl: string;
  private apiPassword: string;
  private content: string;

  constructor(app: App, settings: ShareNoteSettings, content: string) {
      super(app);
      this.apiBaseUrl = settings.apiBaseUrl;
      this.apiPassword = settings.apiPassword;
      this.content = content;
  }

  onOpen() {
      const { contentEl } = this;

      // Стили для модального окна
      contentEl.style.padding = "20px";
      contentEl.style.fontFamily = "Arial, sans-serif";

      // Заголовок
      contentEl.createEl("h2", { text: "Publish Note Settings" });

      // Поле для пароля
      const passwordInput = contentEl.createEl("input", {
          type: "password",
          placeholder: "Enter password (optional)",
      });
      passwordInput.style.width = "100%";
      passwordInput.style.marginBottom = "10px";
      passwordInput.style.padding = "5px";
      passwordInput.style.border = "1px solid #ccc";
      passwordInput.style.borderRadius = "5px";

      // Контейнер для чекбокса и кнопки
      const checkboxContainer = contentEl.createEl("div");
      checkboxContainer.style.marginBottom = "20px";

      // Чекбокс для удаления после прочтения
      const expireCheckbox = checkboxContainer.createEl("input", { type: "checkbox" });
      const expireLabel = checkboxContainer.createEl("label", {
          text: " Delete after one view",
      });
      expireCheckbox.style.marginRight = "5px";

      // Кнопка публикации
      const publishButton = contentEl.createEl("button", { text: "Publish" });
      publishButton.style.marginTop = "10px";
      publishButton.style.padding = "10px 20px";
      publishButton.style.border = "none";
      publishButton.style.borderRadius = "5px";
      publishButton.style.backgroundColor = "#007BFF";
      publishButton.style.color = "#fff";
      publishButton.style.cursor = "pointer";
      publishButton.style.display = "block"; // Кнопка отображается на отдельной строке
      publishButton.style.marginLeft = "auto";
      publishButton.style.marginRight = "auto";

      publishButton.addEventListener("click", async () => {
          const password = passwordInput.value;
          const expireAfterRead = expireCheckbox.checked;

          try {
              const response = await fetch(`${this.apiBaseUrl}/create/`, {
                  method: "POST",
                  headers: {
                      "Content-Type": "application/json",
                      "Authorization": `Bearer ${this.apiPassword}`,
                  },
                  body: JSON.stringify({
                      content: this.content,
                      expire_after_read: expireAfterRead,
                      password: password,
                  }),
              });

              if (!response.ok) {
                  throw new Error("Failed to share note");
              }

              const { url } = await response.json();

              // Копируем ссылку в буфер обмена
              await navigator.clipboard.writeText(url);
              new Notice("Note shared! URL copied to clipboard.");
              this.close(); // Закрываем модальное окно
          } catch (error) {
              new Notice(`Error: ${error.message}`);
          }
      });

      // Добавляем элементы на страницу
      contentEl.appendChild(passwordInput);
      contentEl.appendChild(checkboxContainer);
      contentEl.appendChild(publishButton);
  }

  onClose() {
      const { contentEl } = this;
      contentEl.empty(); // Очищаем содержимое модального окна
  }
}


// Настройки плагина
class ShareNoteSettingTab extends PluginSettingTab {
  plugin: ShareNotePlugin;

  constructor(app: App, plugin: ShareNotePlugin) {
      super(app, plugin); // Передаём app и plugin в родительский конструктор
      this.plugin = plugin;
  }

  display(): void {
      const { containerEl } = this;

      containerEl.empty();

      containerEl.createEl("h2", { text: "Share Note Settings" });

      // Поле для ввода базового URL API
      new Setting(containerEl)
          .setName("API Base URL")
          .setDesc("Set the base URL of your API server.")
          .addText((text) =>
              text
                  .setPlaceholder("http://localhost:8000")
                  .setValue(this.plugin.settings.apiBaseUrl)
                  .onChange(async (value) => {
                      this.plugin.settings.apiBaseUrl = value;
                      await this.plugin.saveSettings();
                  })
          );

      // Поле для ввода пароля
      new Setting(containerEl)
          .setName("API Password")
          .setDesc("Set the password for API authentication.")
          .addText((text) =>
              text
                  .setPlaceholder("Enter your API password")
                  .setValue(this.plugin.settings.apiPassword)
                  .onChange(async (value) => {
                      this.plugin.settings.apiPassword = value;
                      await this.plugin.saveSettings();
                  })
          );
  }
}
