# 🚀 Полный Автопилот GitHub

## 📋 Обзор

Этот проект настроен на **полную автоматизацию** через GitHub Actions. Вы только делаете коммиты — остальное делает система.

---

## ⚙️ Автоматические процессы

### 1. 🔄 CI/CD Pipeline (`ci.yml`)
**Триггер:** Пуш в `main` или `develop`, Pull Request

**Что делает:**
- ✅ Запускает тесты (`pytest`)
- ✅ Собирает `.exe` файл (PyInstaller)
- ✅ Создает релиз с версией `vГГГГ.ММ.ДД.номер`
- ✅ Прикрепляет бинарник к релизу
- ✅ Генерирует описание релиза

### 2. 🤖 AI Auto-Response (`ai-auto-response.yml`)
**Триггер:** Новый Issue или PR

**Что делает:**
- 🔍 Анализирует содержимое
- 🏷️ Автоматически ставит лейблы:
  - `bug` / `status: needs-investigation` — если баг
  - `enhancement` / `type: enhancement` — если фича
  - `question` / `type: question` — если вопрос
- 💬 Пишет умный авто-ответ с планом действий

### 3. 📦 Auto-Dependencies (`auto-dependencies.yml`)
**Триггер:** Каждое понедельник в 03:00 UTC

**Что делает:**
- 🔎 Проверяет обновления зависимостей
- 🔄 Создает PR с обновленным `requirements.txt`
- 🏷️ Добавляет лейбл `dependencies`

### 4. 🛡️ Security Scan (`auto-security.yml`)
**Триггер:** Пуш, PR, ежедневно в 02:00 UTC

**Что делает:**
- 🔒 Сканирует код на уязвимости (Bandit)
- 📦 Проверяет зависимости (Safety, pip-audit)
- 🚨 Создает Issue при критических уязвимостях
- 📊 Загружает отчеты в артефакты

### 5. ✨ Code Quality (`auto-code-quality.yml`)
**Триггер:** Пуш, PR

**Что делает:**
- 🎨 Проверяет форматирование (Black)
- 📝 Линтинг (Flake8)
- 🔤 Сортировка импортов (Isort)
- 🧪 Проверка типов (Mypy)
- 💬 Комментирует PR с результатами

### 6. 🧹 Auto-Stale (`auto-stale.yml`)
**Триггер:** Ежедневно в 01:00 UTC

**Что делает:**
- ⚠️ Помечает старые Issues (14 дней без активности)
- 🔒 Закрывает Issues через 7 дней после пометки
- 📝 Аналогично для PR (7 + 5 дней)
- ❗ Исключает важные лейблы (`pinned`, `security`)

### 7. 🏷️ Auto-Triage (`auto-triage.yml`)
**Триггер:** Новый Issue

**Что делает:**
- 🏷️ Ставит лейблы по ключевым словам (рус/анг)
- 💬 Пишет приветственный ответ

### 8. 📝 Auto-Release Notes (`auto-release-notes.yml`)
**Триггер:** Публикация релиза

**Что делает:**
- 📢 Логирует информацию о релизе
- 🔄 (Можно расширить для обновления CHANGELOG)

---

## 🎯 Ваш рабочий процесс

### Вы делаете:
```bash
git add .
git commit -m "Описание изменений"
git push origin main
```

### GitHub делает автоматически:
1. ✅ Тестирует код
2. ✅ Проверяет качество
3. ✅ Сканирует безопасность
4. ✅ Собирает `.exe`
5. ✅ Создает релиз на GitHub
6. ✅ Уведомляет пользователей

---

## 📊 Статус автоматизации

| Процесс | Статус | Файл |
|---------|--------|------|
| CI/CD | ✅ Активен | `ci.yml` |
| AI-ответы | ✅ Активен | `ai-auto-response.yml` |
| Обновление зависимостей | ✅ Активен | `auto-dependencies.yml` |
| Security Scan | ✅ Активен | `auto-security.yml` |
| Code Quality | ✅ Активен | `auto-code-quality.yml` |
| Stale Issues | ✅ Активен | `auto-stale.yml` |
| Auto-Triage | ✅ Активен | `auto-triage.yml` |
| Release Notes | ✅ Активен | `auto-release-notes.yml` |

---

## 🔧 Настройка (опционально)

### Для уведомлений в Telegram/Discord:
Добавьте webhook в `ci.yml`:
```yaml
- name: Notify Discord
  run: |
    curl -X POST ${{ secrets.DISCORD_WEBHOOK }} \
      -H "Content-Type: application/json" \
      -d '{"content": "🚀 Новый релиз: ${{ steps.version.outputs.VERSION }}"}'
```

### Для авто-мерджа зависимостей:
Добавьте [Dependabot](https://docs.github.com/en/code-security/dependabot) в `.github/dependabot.yml`.

---

## 📞 Поддержка

Все процессы работают автономно. Если нужно что-то изменить — редактируйте файлы в `.github/workflows/`.

---

*🤖 Full Autopilot System v2.0*
