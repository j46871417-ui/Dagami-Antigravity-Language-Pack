"""
Dagami Antigravity Language Pack — Generator of language packs.
Populates standard language packs for ru, zh, es, ja, de, fr.
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).parent
LANG_ROOT = REPO_ROOT / "translations" / "languages"

METADATA = {
    "ru": {
        "code": "ru",
        "name": "Russian",
        "nativeName": "Русский",
        "version": "1.0.0",
        "translatorTarget": "ru",
        "flag": "🇷🇺",
        "buttonLabel": "🌐 RU",
        "buttonTitle": "Перевести размышления на русский",
        "autoLabelOn": "⚡ Авто: ВКЛ",
        "autoLabelOff": "⚡ Авто: ВЫКЛ",
        "autoTitle": "Автоперевод мыслей",
        "originalButton": "🌐 EN",
        "originalTitle": "Показать оригинал на английском",
        "vscodeLocale": "ru",
    },
    "zh": {
        "code": "zh",
        "name": "Chinese (Simplified)",
        "nativeName": "简体中文",
        "version": "1.0.0",
        "translatorTarget": "zh-CN",
        "flag": "🇨🇳",
        "buttonLabel": "🌐 ZH",
        "buttonTitle": "翻译思考过程为中文",
        "autoLabelOn": "⚡ 自动: 开",
        "autoLabelOff": "⚡ 自动: 关",
        "autoTitle": "自动翻译思考过程",
        "originalButton": "🌐 EN",
        "originalTitle": "显示英文原文",
        "vscodeLocale": "zh-cn",
    },
    "es": {
        "code": "es",
        "name": "Spanish",
        "nativeName": "Español",
        "version": "1.0.0",
        "translatorTarget": "es",
        "flag": "🇪🇸",
        "buttonLabel": "🌐 ES",
        "buttonTitle": "Traducir pensamientos al español",
        "autoLabelOn": "⚡ Auto: SÍ",
        "autoLabelOff": "⚡ Auto: NO",
        "autoTitle": "Traducción automática de pensamientos",
        "originalButton": "🌐 EN",
        "originalTitle": "Mostrar original en inglés",
        "vscodeLocale": "es",
    },
    "ja": {
        "code": "ja",
        "name": "Japanese",
        "nativeName": "日本語",
        "version": "1.0.0",
        "translatorTarget": "ja",
        "flag": "🇯🇵",
        "buttonLabel": "🌐 JA",
        "buttonTitle": "思考プロセスを日本語に翻訳",
        "autoLabelOn": "⚡ 自動: ON",
        "autoLabelOff": "⚡ 自動: OFF",
        "autoTitle": "思考プロセスの自動翻訳",
        "originalButton": "🌐 EN",
        "originalTitle": "オリジナルの英語を表示",
        "vscodeLocale": "ja",
    },
    "de": {
        "code": "de",
        "name": "German",
        "nativeName": "Deutsch",
        "version": "1.0.0",
        "translatorTarget": "de",
        "flag": "🇩🇪",
        "buttonLabel": "🌐 DE",
        "buttonTitle": "Gedankengang ins Deutsche übersetzen",
        "autoLabelOn": "⚡ Auto: AN",
        "autoLabelOff": "⚡ Auto: AUS",
        "autoTitle": "Automatische Übersetzung des Gedankengangs",
        "originalButton": "🌐 EN",
        "originalTitle": "Original auf Englisch anzeigen",
        "vscodeLocale": "de",
    },
    "fr": {
        "code": "fr",
        "name": "French",
        "nativeName": "Français",
        "version": "1.0.0",
        "translatorTarget": "fr",
        "flag": "🇫🇷",
        "buttonLabel": "🌐 FR",
        "buttonTitle": "Traduire le processus de réflexion en français",
        "autoLabelOn": "⚡ Auto: ACTIF",
        "autoLabelOff": "⚡ Auto: DÉSACTIF",
        "autoTitle": "Traduction automatique de la réflexion",
        "originalButton": "🌐 EN",
        "originalTitle": "Afficher l'original en anglais",
        "vscodeLocale": "fr",
    },
}

# Base UI phrases dictionary for multilingual mapping
COMMON_TERMS = {
    # Navigation & Core
    "New Conversation": {"zh": "新建对话", "es": "Nueva conversación", "ja": "新しい会話", "de": "Neue Unterhaltung", "fr": "Nouvelle conversation"},
    "New conversation": {"zh": "新建对话", "es": "Nueva conversación", "ja": "新しい会話", "de": "Neue Unterhaltung", "fr": "Nouvelle conversation"},
    "Conversation History": {"zh": "对话历史", "es": "Historial de conversaciones", "ja": "会話の履歴", "de": "Unterhaltungsverlauf", "fr": "Historique des conversations"},
    "Conversation history": {"zh": "对话历史", "es": "Historial de conversaciones", "ja": "会話の履歴", "de": "Unterhaltungsverlauf", "fr": "Historique des conversations"},
    "Projects": {"zh": "项目", "es": "Proyectos", "ja": "プロジェクト", "de": "Projekte", "fr": "Projets"},
    "Scheduled Tasks": {"zh": "定时任务", "es": "Tareas programadas", "ja": "スケジュールされたタスク", "de": "Geplante Aufgaben", "fr": "Tâches planifiées"},
    "Scheduled tasks": {"zh": "定时任务", "es": "Tareas programadas", "ja": "スケジュールされたタスク", "de": "Geplante Aufgaben", "fr": "Tâches planifiées"},
    "Skills & Customizations": {"zh": "技能与自定义", "es": "Habilidades y personalizaciones", "ja": "スキルとカスタマイズ", "de": "Fähigkeiten & Anpassungen", "fr": "Compétences et personnalisations"},
    "Skills & customizations": {"zh": "技能与自定义", "es": "Habilidades y personalizaciones", "ja": "スキルとカスタマイズ", "de": "Fähigkeiten & Anpassungen", "fr": "Compétences et personnalisations"},
    "Customizations": {"zh": "自定义", "es": "Personalizaciones", "ja": "カスタマイズ", "de": "Anpassungen", "fr": "Personnalisations"},
    "Customization": {"zh": "自定义", "es": "Personalización", "ja": "カスタマイズ", "de": "Anpassung", "fr": "Personnalisation"},
    "Settings": {"zh": "设置", "es": "Configuración", "ja": "設定", "de": "Einstellungen", "fr": "Paramètres"},
    "UI Plugins": {"zh": "UI 插件", "es": "Plugins de interfaz", "ja": "UIプラグイン", "de": "UI-Plugins", "fr": "Plugins d'interface"},
    "UI plugins": {"zh": "UI 插件", "es": "Plugins de interfaz", "ja": "UIプラグイン", "de": "UI-Plugins", "fr": "Plugins d'interface"},
    "Automations": {"zh": "自动化", "es": "Automatizaciones", "ja": "自動化", "de": "Automatisierungen", "fr": "Automatisations"},
    "Recent Conversations": {"zh": "最近对话", "es": "Conversaciones recientes", "ja": "最近の会話", "de": "Letzte Unterhaltungen", "fr": "Conversations récentes"},
    "Recent conversations": {"zh": "最近对话", "es": "Conversaciones recientes", "ja": "最近の会話", "de": "Letzte Unterhaltungen", "fr": "Conversations récentes"},
    "Recent": {"zh": "最近", "es": "Recientes", "ja": "最近", "de": "Zuletzt", "fr": "Récents"},
    "History": {"zh": "历史记录", "es": "Historial", "ja": "履歴", "de": "Verlauf", "fr": "Historique"},
    "Running agents": {"zh": "运行中的智能体", "es": "Agentes en ejecución", "ja": "実行中のエージェント", "de": "Laufende Agenten", "fr": "Agents en cours"},
    "No agents running": {"zh": "没有运行中的智能体", "es": "No hay agentes en ejecución", "ja": "実行中のエージェントはありません", "de": "Keine Agenten aktiv", "fr": "Aucun agent en cours"},
    "Open Settings": {"zh": "打开设置", "es": "Abrir configuración", "ja": "設定を開く", "de": "Einstellungen öffnen", "fr": "Ouvrir les paramètres"},
    "Global Settings": {"zh": "全局设置", "es": "Configuración global", "ja": "グローバル設定", "de": "Globale Einstellungen", "fr": "Paramètres généraux"},
    "Project Settings": {"zh": "项目设置", "es": "Configuración del proyecto", "ja": "プロジェクト設定", "de": "Projekteinstellungen", "fr": "Paramètres du projet"},
    "Restart to Update": {"zh": "重启以更新", "es": "Reiniciar para actualizar", "ja": "再起動して更新", "de": "Neu starten zum Aktualisieren", "fr": "Redémarrer pour mettre à jour"},
    "Open IDE": {"zh": "打开 IDE", "es": "Abrir IDE", "ja": "IDEを開く", "de": "IDE öffnen", "fr": "Ouvrir l'IDE"},
    "Open in IDE": {"zh": "在 IDE 中打开", "es": "Abrir en el IDE", "ja": "IDEで開く", "de": "In IDE öffnen", "fr": "Ouvrir dans l'IDE"},
    "Open Antigravity IDE": {"zh": "打开 Antigravity IDE", "es": "Abrir Antigravity IDE", "ja": "Antigravity IDEを開く", "de": "Antigravity IDE öffnen", "fr": "Ouvrir Antigravity IDE"},
    "Ask anything, @ to mention, / for actions": {"zh": "输入任何问题，使用 @ 提及，/ 执行操作", "es": "Pregunta lo que sea, usa @ para mencionar, / para acciones", "ja": "何でも質問、@でメンション、/でアクション", "de": "Fragen Sie etwas, @ zum Erwähnen, / für Aktionen", "fr": "Posez une question, @ pour mentionner, / pour les actions"},
    
    # Desktop Menu & Tray
    "File": {"zh": "文件", "es": "Archivo", "ja": "ファイル", "de": "Datei", "fr": "Fichier"},
    "Edit": {"zh": "编辑", "es": "Edición", "ja": "編集", "de": "Bearbeiten", "fr": "Modifier"},
    "View": {"zh": "视图", "es": "Ver", "ja": "表示", "de": "Ansicht", "fr": "Affichage"},
    "Window": {"zh": "窗口", "es": "Ventana", "ja": "ウィンドウ", "de": "Fenster", "fr": "Fenêtre"},
    "Help": {"zh": "帮助", "es": "Ayuda", "ja": "ヘルプ", "de": "Hilfe", "fr": "Aide"},
    "New Window": {"zh": "新建窗口", "es": "Nueva ventana", "ja": "新しいウィンドウ", "de": "Neues Fenster", "fr": "Nouvelle fenêtre"},
    "Docs": {"zh": "文档", "es": "Documentación", "ja": "ドキュメント", "de": "Dokumentation", "fr": "Documentation"},
    "Check for Updates": {"zh": "检查更新", "es": "Buscar actualizaciones", "ja": "アップデートを確認", "de": "Nach Updates suchen", "fr": "Rechercher les mises à jour"},
    "Connect to WSL": {"zh": "连接到 WSL", "es": "Conectar a WSL", "ja": "WSLに接続", "de": "Mit WSL verbinden", "fr": "Se connecter à WSL"},
    "Reopen Locally": {"zh": "在本地重新打开", "es": "Reabrir localmente", "ja": "ローカルで再度開く", "de": "Lokal erneut öffnen", "fr": "Rouvrir localement"},
    "Quit": {"zh": "退出", "es": "Salir", "ja": "終了", "de": "Beenden", "fr": "Quitter"},
    "agent running": {"zh": "个智能体运行中", "es": "agente en ejecución", "ja": "件のエージェントが実行中", "de": "Agent aktiv", "fr": "agent en cours"},
    "agents running": {"zh": "个智能体运行中", "es": "agentes en ejecución", "ja": "件のエージェントが実行中", "de": "Agenten aktiv", "fr": "agents en cours"},

    # Wizard
    "Welcome to Antigravity": {"zh": "欢迎使用 Antigravity", "es": "Bienvenido a Antigravity", "ja": "Antigravityへようこそ", "de": "Willkommen bei Antigravity", "fr": "Bienvenue sur Antigravity"},
    "Setting up…": {"zh": "正在配置…", "es": "Configurando…", "ja": "設定中…", "de": "Einrichten…", "fr": "Configuration…"},
    "Welcome to the new Antigravity!": {"zh": "欢迎使用全新的 Antigravity！", "es": "¡Bienvenido al nuevo Antigravity!", "ja": "新しいAntigravityへようこそ！", "de": "Willkommen beim neuen Antigravity!", "fr": "Bienvenue dans le nouvel Antigravity !"},
    "Download the Antigravity IDE": {"zh": "下载 Antigravity IDE", "es": "Descargar Antigravity IDE", "ja": "Antigravity IDEをダウンロード", "de": "Antigravity IDE herunterladen", "fr": "Télécharger Antigravity IDE"},
    "Explore the new Antigravity": {"zh": "探索全新的 Antigravity", "es": "Explorar el nuevo Antigravity", "ja": "新しいAntigravityを体験", "de": "Das neue Antigravity entdecken", "fr": "Explorer le nouvel Antigravity"},

    # Actions & Workspaces
    "Workspaces": {"zh": "工作区", "es": "Espacios de trabajo", "ja": "ワークスペース", "de": "Arbeitsbereiche", "fr": "Espaces de travail"},
    "Workspace": {"zh": "工作区", "es": "Espacio de trabajo", "ja": "ワークスペース", "de": "Arbeitsbereich", "fr": "Espace de travail"},
    "All Workspaces": {"zh": "所有工作区", "es": "Todos los espacios", "ja": "すべてのワークスペース", "de": "Alle Arbeitsbereiche", "fr": "Tous les espaces"},
    "Current Workspace": {"zh": "当前工作区", "es": "Espacio actual", "ja": "現在のワークスペース", "de": "Aktueller Arbeitsbereich", "fr": "Espace de travail actuel"},
    "Add Workspace": {"zh": "添加工作区", "es": "Añadir espacio", "ja": "ワークスペースを追加", "de": "Arbeitsbereich hinzufügen", "fr": "Ajouter un espace"},
    "New Workspace": {"zh": "新建工作区", "es": "Nuevo espacio de trabajo", "ja": "新規ワークスペース", "de": "Neuer Arbeitsbereich", "fr": "Nouvel espace de travail"},
    "Archive Workspace": {"zh": "归档工作区", "es": "Archivar espacio", "ja": "ワークスペースをアーカイブ", "de": "Arbeitsbereich archivieren", "fr": "Archiver l'espace"},
    "Select Theme": {"zh": "选择主题", "es": "Seleccionar tema", "ja": "テーマを選択", "de": "Design auswählen", "fr": "Sélectionner un thème"},
    "Light": {"zh": "浅色", "es": "Claro", "ja": "ライト", "de": "Hell", "fr": "Clair"},
    "Dark": {"zh": "深色", "es": "Oscuro", "ja": "ダーク", "de": "Dunkel", "fr": "Sombre"},
    "System": {"zh": "跟随系统", "es": "Sistema", "ja": "システム", "de": "System", "fr": "Système"},
    "Inherit": {"zh": "继承系统", "es": "Heredar del sistema", "ja": "システムに準拠", "de": "Vom System übernehmen", "fr": "Hériter du système"},
    "Previous": {"zh": "上一步", "es": "Anterior", "ja": "前へ", "de": "Zurück", "fr": "Précédent"},
    "Next": {"zh": "下一步", "es": "Siguiente", "ja": "次へ", "de": "Weiter", "fr": "Suivant"},
    "Get Started": {"zh": "开始使用", "es": "Empezar", "ja": "始める", "de": "Loslegen", "fr": "Commencer"},
    "Finish": {"zh": "完成", "es": "Finalizar", "ja": "完了", "de": "Fertigstellen", "fr": "Terminer"},
    "Skip": {"zh": "跳过", "es": "Omitir", "ja": "スキップ", "de": "Überspringen", "fr": "Ignorer"},
    "Continue": {"zh": "继续", "es": "Continuar", "ja": "続行", "de": "Fortfahren", "fr": "Continuer"},
    "Back": {"zh": "返回", "es": "Atrás", "ja": "戻る", "de": "Zurück", "fr": "Retour"},
    "Save": {"zh": "保存", "es": "Guardar", "ja": "保存", "de": "Speichern", "fr": "Enregistrer"},
    "Cancel": {"zh": "取消", "es": "Cancelar", "ja": "キャンセル", "de": "Abbrechen", "fr": "Annuler"},
    "Delete": {"zh": "删除", "es": "Eliminar", "ja": "削除", "de": "Löschen", "fr": "Supprimer"},
    "Close": {"zh": "关闭", "es": "Cerrar", "ja": "閉じる", "de": "Schließen", "fr": "Fermer"},
    "Copy": {"zh": "复制", "es": "Copiar", "ja": "コピー", "de": "Kopieren", "fr": "Copier"},
    "Copied": {"zh": "已复制", "es": "Copiado", "ja": "コピーしました", "de": "Kopiert", "fr": "Copié"},

    # Settings Tabs & Categories
    "Account": {"zh": "账户", "es": "Cuenta", "ja": "アカウント", "de": "Konto", "fr": "Compte"},
    "Permissions": {"zh": "权限", "es": "Permisos", "ja": "権限", "de": "Berechtigungen", "fr": "Autorisations"},
    "General": {"zh": "常规", "es": "General", "ja": "一般", "de": "Allgemein", "fr": "Général"},
    "Appearance": {"zh": "外观", "es": "Apariencia", "ja": "外観", "de": "Erscheinungsbild", "fr": "Apparence"},
    "Editor": {"zh": "编辑器", "es": "Editor", "ja": "エディタ", "de": "Editor", "fr": "Éditeur"},
    "Browser": {"zh": "浏览器", "es": "Navegador", "ja": "ブラウザ", "de": "Browser", "fr": "Navigateur"},
    "Notifications": {"zh": "通知", "es": "Notificaciones", "ja": "通知", "de": "Benachrichtigungen", "fr": "Notifications"},
    "Models": {"zh": "模型", "es": "Modelos", "ja": "モデル", "de": "Modelle", "fr": "Modèles"},
    "Model Selection": {"zh": "模型选择", "es": "Selección de modelo", "ja": "モデルの選択", "de": "Modellauswahl", "fr": "Sélection du modèle"},
    "Select Model": {"zh": "选择模型", "es": "Seleccionar modelo", "ja": "モデルを選択", "de": "Modell wählen", "fr": "Sélectionner le modèle"},
    "Default Model": {"zh": "默认模型", "es": "Modelo predeterminado", "ja": "デフォルトモデル", "de": "Standardmodell", "fr": "Modèle par défaut"},
    "Shortcuts": {"zh": "快捷键", "es": "Atajos de teclado", "ja": "キーボードショートカット", "de": "Tastenkombinationen", "fr": "Raccourcis"},
    "Feedback": {"zh": "反馈", "es": "Comentarios", "ja": "フィードバック", "de": "Feedback", "fr": "Commentaires"},
    "Provide Feedback": {"zh": "提交反馈", "es": "Enviar comentarios", "ja": "フィードバックを送信", "de": "Feedback geben", "fr": "Donner un avis"},
    
    # Decisions / Buttons
    "Always Proceed": {"zh": "始终继续", "es": "Continuar siempre", "ja": "常に続行", "de": "Immer fortfahren", "fr": "Toujours continuer"},
    "Always Ask": {"zh": "始终询问", "es": "Preguntar siempre", "ja": "常に確認", "de": "Immer nachfragen", "fr": "Toujours demander"},
    "Always ask": {"zh": "始终询问", "es": "Preguntar siempre", "ja": "常に確認", "de": "Immer nachfragen", "fr": "Toujours demander"},
    "Ask First": {"zh": "先询问", "es": "Preguntar primero", "ja": "最初に確認", "de": "Zuerst fragen", "fr": "Demander d'abord"},
    "Request Review": {"zh": "请求审查", "es": "Solicitar revisión", "ja": "レビューをリクエスト", "de": "Überprüfung anfordern", "fr": "Demander une révision"},
    "Always allow": {"zh": "始终允许", "es": "Permitir siempre", "ja": "常に許可", "de": "Immer erlauben", "fr": "Toujours autoriser"},
    "Always Allow": {"zh": "始终允许", "es": "Permitir siempre", "ja": "常に許可", "de": "Immer erlauben", "fr": "Toujours autoriser"},
    "Allow Once": {"zh": "允许一次", "es": "Permitir una vez", "ja": "1回のみ許可", "de": "Einmal erlauben", "fr": "Autoriser une fois"},
    "Allow once": {"zh": "允许一次", "es": "Permitir una vez", "ja": "1回のみ許可", "de": "Einmal erlauben", "fr": "Autoriser une fois"},
    "Deny": {"zh": "拒绝", "es": "Denegar", "ja": "拒否", "de": "Ablehnen", "fr": "Refuser"},
    "Approve": {"zh": "批准", "es": "Aprobar", "ja": "承認", "de": "Genehmigen", "fr": "Approuver"},
    "Reject": {"zh": "拒绝", "es": "Rechazar", "ja": "却下", "de": "Verwerfen", "fr": "Rejeter"},
    "Allow": {"zh": "允许", "es": "Permitir", "ja": "許可", "de": "Erlauben", "fr": "Autoriser"},
    "Action required": {"zh": "需要操作", "es": "Acción requerida", "ja": "アクションが必要です", "de": "Aktion erforderlich", "fr": "Action requise"},
    
    # Tool Verbs & Statuses
    "Analyzed": {"zh": "已分析", "es": "Analizado", "ja": "分析完了", "de": "Analysiert", "fr": "Analysé"},
    "Analyzing": {"zh": "正在分析...", "es": "Analizando...", "ja": "分析中...", "de": "Analysiert...", "fr": "Analyse en cours..."},
    "Read": {"zh": "已读取", "es": "Leído", "ja": "読み込み完了", "de": "Gelesen", "fr": "Lu"},
    "Reading": {"zh": "正在读取...", "es": "Leyendo...", "ja": "読み込み中...", "de": "Liest...", "fr": "Lecture en cours..."},
    "Edited": {"zh": "已编辑", "es": "Editado", "ja": "編集完了", "de": "Bearbeitet", "fr": "Modifié"},
    "Editing": {"zh": "正在编辑...", "es": "Editando...", "ja": "編集中...", "de": "Bearbeitet...", "fr": "Modification en cours..."},
    "Executed": {"zh": "已执行", "es": "Ejecutado", "ja": "実行完了", "de": "Ausgeführt", "fr": "Exécuté"},
    "Executing": {"zh": "正在执行...", "es": "Ejecutando...", "ja": "実行中...", "de": "Führt aus...", "fr": "Exécution en cours..."},
    "Searched": {"zh": "已搜索", "es": "Buscado", "ja": "検索完了", "de": "Gesucht", "fr": "Recherché"},
    "Searching": {"zh": "正在搜索...", "es": "Buscando...", "ja": "検索中...", "de": "Sucht...", "fr": "Recherche en cours..."},
    "Built": {"zh": "已构建", "es": "Compilado", "ja": "ビルド完了", "de": "Erstellt", "fr": "Compilé"},
    "Building": {"zh": "正在构建...", "es": "Compilando...", "ja": "ビルド中...", "de": "Erstellt...", "fr": "Compilation en cours..."},
    "Created": {"zh": "已创建", "es": "Creado", "ja": "作成完了", "de": "Erstellt", "fr": "Créé"},
    "Creating": {"zh": "正在创建...", "es": "Creando...", "ja": "作成中...", "de": "Erstellt...", "fr": "Création en cours..."},
    "Deleted": {"zh": "已删除", "es": "Eliminado", "ja": "削除完了", "de": "Gelöscht", "fr": "Supprimé"},
    "Deleting": {"zh": "正在删除...", "es": "Eliminando...", "ja": "削除中...", "de": "Löscht...", "fr": "Suppression en cours..."},
}


def build_packs():
    # Read Russian dictionary as base key set
    ru_dict_file = LANG_ROOT / "ru" / "dict.json"
    ru_dict = {}
    if ru_dict_file.exists():
        with open(ru_dict_file, "r", encoding="utf-8") as f:
            ru_dict = json.load(f)

    for lang_code, meta in METADATA.items():
        lang_dir = LANG_ROOT / lang_code
        lang_dir.mkdir(parents=True, exist_ok=True)

        # Write metadata
        with open(lang_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # Build dictionary
        if lang_code == "ru":
            lang_dict = ru_dict
        else:
            lang_dict = {}
            for k, trans_map in COMMON_TERMS.items():
                if lang_code in trans_map:
                    lang_dict[k] = trans_map[lang_code]
            # Copy all remaining keys from ru_dict if not translated yet
            # In future updates or --update, keys can be extended
            for k in ru_dict:
                if k not in lang_dict:
                    if k in COMMON_TERMS and lang_code in COMMON_TERMS[k]:
                        lang_dict[k] = COMMON_TERMS[k][lang_code]

        with open(lang_dir / "dict.json", "w", encoding="utf-8") as f:
            json.dump(lang_dict, f, ensure_ascii=False, indent=2)

        # Build desktop strings (menu, tray, wizard)
        desktop = {
            "menu": {
                "New Window": COMMON_TERMS.get("New Window", {}).get(lang_code, "New Window") if lang_code != "ru" else "Новое окно",
                "Docs": COMMON_TERMS.get("Docs", {}).get(lang_code, "Docs") if lang_code != "ru" else "Документация",
                "Check for Updates": COMMON_TERMS.get("Check for Updates", {}).get(lang_code, "Check for Updates") if lang_code != "ru" else "Проверить обновления",
                "Connect to WSL": COMMON_TERMS.get("Connect to WSL", {}).get(lang_code, "Connect to WSL") if lang_code != "ru" else "Подключиться к WSL",
                "Reopen Locally": COMMON_TERMS.get("Reopen Locally", {}).get(lang_code, "Reopen Locally") if lang_code != "ru" else "Переоткрыть локально",
            },
            "tray": {
                "No agents running": COMMON_TERMS.get("No agents running", {}).get(lang_code, "No agents running") if lang_code != "ru" else "Нет запущенных агентов",
                "agent running": COMMON_TERMS.get("agent running", {}).get(lang_code, "agent running") if lang_code != "ru" else "агент запущен",
                "agents running": COMMON_TERMS.get("agents running", {}).get(lang_code, "agents running") if lang_code != "ru" else "агентов запущено",
                "Quit": COMMON_TERMS.get("Quit", {}).get(lang_code, "Quit") if lang_code != "ru" else "Выход",
            },
            "wizard": {
                "Welcome to Antigravity": COMMON_TERMS.get("Welcome to Antigravity", {}).get(lang_code, "Welcome to Antigravity") if lang_code != "ru" else "Добро пожаловать в Antigravity",
                "Setting up…": COMMON_TERMS.get("Setting up…", {}).get(lang_code, "Setting up…") if lang_code != "ru" else "Настройка…",
                "Welcome to the new Antigravity!": COMMON_TERMS.get("Welcome to the new Antigravity!", {}).get(lang_code, "Welcome to the new Antigravity!") if lang_code != "ru" else "Добро пожаловать в новый Antigravity!",
                "Download the Antigravity IDE": COMMON_TERMS.get("Download the Antigravity IDE", {}).get(lang_code, "Download the Antigravity IDE") if lang_code != "ru" else "Скачать Antigravity IDE",
                "Explore the new Antigravity": COMMON_TERMS.get("Explore the new Antigravity", {}).get(lang_code, "Explore the new Antigravity") if lang_code != "ru" else "Познакомиться с новым Antigravity",
            }
        }
        with open(lang_dir / "desktop.json", "w", encoding="utf-8") as f:
            json.dump(desktop, f, ensure_ascii=False, indent=2)

        if lang_code == "ru":
            desktop = json.loads((LANG_ROOT.parent / "desktop_strings.json").read_text("utf-8")) | desktop
            (lang_dir / "desktop.json").write_text(json.dumps(desktop, ensure_ascii=False, indent=2), "utf-8")

        # Build IDE commands
        ide_data = {
            "commands": {
                "antigravity.startAgent": {lang_code: COMMON_TERMS.get("Running agents", {}).get(lang_code, "Start Agent")},
                "antigravity.openSettings": {lang_code: COMMON_TERMS.get("Open Settings", {}).get(lang_code, "Open Settings")},
            }
        }
        if lang_code == "ru":
            ide_data = json.loads((LANG_ROOT.parent / "ide_strings.json").read_text("utf-8"))
        with open(lang_dir / "ide.json", "w", encoding="utf-8") as f:
            json.dump(ide_data, f, ensure_ascii=False, indent=2)

        print(f"Generated language pack for: {lang_code} ({meta['nativeName']}) - {len(lang_dict)} terms")


if __name__ == "__main__":
    build_packs()
