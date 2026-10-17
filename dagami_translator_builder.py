"""
Dagami Antigravity Language Pack — Dynamic Runtime Translator Builder.
Generates JavaScript code injected into dist/preload.js for any supported language.
"""

import json
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    REPO_ROOT = Path(sys._MEIPASS)
else:
    REPO_ROOT = Path(__file__).resolve().parent

LANG_ROOT = REPO_ROOT / "translations" / "languages"
PRELOAD_MARKER = "// Antigravity UI Runtime Localizer"

RULE_TEMPLATES = {
    "ru": [
        ('^Searching for\\s+(.+)$', 'return "Поиск " + m[1];'),
        ('^Searched for\\s+(.+)$', 'return "Поиск завершен: " + m[1];'),
        ('^Searching Moma for\\s+(.+)$', 'return "Поиск в Moma: " + m[1];'),
        ('^Searched Moma for\\s+(.+)$', 'return "Поиск в Moma завершен: " + m[1];'),
        ('^Reading\\s+(.+)$', 'return "Чтение " + m[1];'),
        ('^Read\\s+(.+)$', 'return "Прочитано: " + m[1];'),
        ('^Editing\\s+(.+)$', 'return "Редактирование " + m[1];'),
        ('^Edited\\s+(.+)$', 'return "Отредактировано: " + m[1];'),
        ('^Writing\\s+(.+)$', 'return "Запись " + m[1];'),
        ('^Written\\s+(.+)$', 'return "Записано: " + m[1];'),
        ('^Running\\s+(.+)$', 'return "Выполнение " + m[1];'),
        ('^Ran\\s+(.+)$', 'return "Выполнено: " + m[1];'),
        ('^Executing\\s+(.+)$', 'return "Выполнение " + m[1];'),
        ('^Executed\\s+(.+)$', 'return "Выполнено: " + m[1];'),
        ('^Creating\\s+(.+)$', 'return "Создание " + m[1];'),
        ('^Created\\s+(.+)$', 'return "Создано: " + m[1];'),
        ('^Deleting\\s+(.+)$', 'return "Удаление " + m[1];'),
        ('^Deleted\\s+(.+)$', 'return "Удалено: " + m[1];'),
        ('^Analyzing\\s+(.+)$', 'return "Анализ " + m[1];'),
        ('^Analyzed\\s+(.+)$', 'return "Проанализировано: " + m[1];'),
        ('^Listing\\s+(.+)$', 'return "Просмотр каталога " + m[1];'),
        ('^Listed\\s+(.+)$', 'return "Просмотрен каталог: " + m[1];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Размышлял " + m[1] + " с" + m[2];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Размышлял " + m[1] + " мин" + m[2];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:h|hours?)(.*)$', 'return "Размышлял " + m[1] + " ч" + m[2];'),
        ('^Thinking for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Размышляет " + m[1] + " с" + m[2];'),
        ('^Thinking for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Размышляет " + m[1] + " мин" + m[2];'),
        ('^Worked for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Работал " + m[1] + " с" + m[2];'),
        ('^Worked for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Работал " + m[1] + " мин" + m[2];'),
        ('^Working for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Работает " + m[1] + " с" + m[2];'),
        ('^Working for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Работает " + m[1] + " мин" + m[2];'),
        ('^Ran for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Выполнялся " + m[1] + " с" + m[2];'),
        ('^Ran for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Выполнялся " + m[1] + " мин" + m[2];'),
        ('^Step\\s+(\\d+)\\s+of\\s+(\\d+)$', 'return "Шаг " + m[1] + " из " + m[2];'),
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "Добавлено строк: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "Удалено строк: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "Изменено строк: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*changed$', 'return "Изменено файлов: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*created$', 'return "Создано файлов: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*deleted$', 'return "Удалено файлов: " + m[1];'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return "Запущено агентов: " + m[1];'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " из " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " эл.";'),
        ('^([0-9]+)\\s+results?$', 'return m[1] + " рез.";'),
        ('^Clicking element\\s+"?(.+?)"?$', 'return "Клик по элементу \\"" + m[1] + "\\"";'),
        ('^Clicked element\\s+"?(.+?)"?$', 'return "Кликнут элемент \\"" + m[1] + "\\"";'),
        ('^Error while running:\\s*(.*)$', 'return "Ошибка при выполнении: " + m[1];'),
    ],
    "zh": [
        ('^Searching for\\s+(.+)$', 'return "正在搜索 " + m[1];'),
        ('^Searched for\\s+(.+)$', 'return "已搜索: " + m[1];'),
        ('^Reading\\s+(.+)$', 'return "正在读取 " + m[1];'),
        ('^Read\\s+(.+)$', 'return "已读取: " + m[1];'),
        ('^Editing\\s+(.+)$', 'return "正在编辑 " + m[1];'),
        ('^Edited\\s+(.+)$', 'return "已编辑: " + m[1];'),
        ('^Writing\\s+(.+)$', 'return "正在写入 " + m[1];'),
        ('^Running\\s+(.+)$', 'return "正在运行 " + m[1];'),
        ('^Ran\\s+(.+)$', 'return "已运行: " + m[1];'),
        ('^Executing\\s+(.+)$', 'return "正在执行 " + m[1];'),
        ('^Executed\\s+(.+)$', 'return "已执行: " + m[1];'),
        ('^Creating\\s+(.+)$', 'return "正在创建 " + m[1];'),
        ('^Created\\s+(.+)$', 'return "已创建: " + m[1];'),
        ('^Deleting\\s+(.+)$', 'return "正在删除 " + m[1];'),
        ('^Deleted\\s+(.+)$', 'return "已删除: " + m[1];'),
        ('^Analyzing\\s+(.+)$', 'return "正在分析 " + m[1];'),
        ('^Analyzed\\s+(.+)$', 'return "已分析: " + m[1];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "思考了 " + m[1] + " 秒" + m[2];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "思考了 " + m[1] + " 分钟" + m[2];'),
        ('^Thinking for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "正在思考 " + m[1] + " 秒" + m[2];'),
        ('^Worked for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "工作了 " + m[1] + " 秒" + m[2];'),
        ('^Step\\s+(\\d+)\\s+of\\s+(\\d+)$', 'return "第 " + m[1] + " 步，共 " + m[2] + " 步";'),
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "添加了 " + m[1] + " 行";'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "删除了 " + m[1] + " 行";'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "修改了 " + m[1] + " 行";'),
        ('^([0-9]+)\\s*files?\\s*changed$', 'return "修改了 " + m[1] + " 个文件";'),
        ('^([0-9]+)\\s*files?\\s*created$', 'return "创建了 " + m[1] + " 个文件";'),
        ('^([0-9]+)\\s*files?\\s*deleted$', 'return "删除了 " + m[1] + " 个文件";'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return m[1] + " 个智能体运行中";'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " / " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " 项";'),
        ('^([0-9]+)\\s+results?$', 'return m[1] + " 条结果";'),
    ],
    "es": [
        ('^Searching for\\s+(.+)$', 'return "Buscando " + m[1];'),
        ('^Searched for\\s+(.+)$', 'return "Búsqueda finalizada: " + m[1];'),
        ('^Reading\\s+(.+)$', 'return "Leyendo " + m[1];'),
        ('^Read\\s+(.+)$', 'return "Leído: " + m[1];'),
        ('^Editing\\s+(.+)$', 'return "Editando " + m[1];'),
        ('^Edited\\s+(.+)$', 'return "Editado: " + m[1];'),
        ('^Writing\\s+(.+)$', 'return "Escribiendo " + m[1];'),
        ('^Running\\s+(.+)$', 'return "Ejecutando " + m[1];'),
        ('^Ran\\s+(.+)$', 'return "Ejecutado: " + m[1];'),
        ('^Executing\\s+(.+)$', 'return "Ejecutando " + m[1];'),
        ('^Executed\\s+(.+)$', 'return "Ejecutado: " + m[1];'),
        ('^Creating\\s+(.+)$', 'return "Creando " + m[1];'),
        ('^Created\\s+(.+)$', 'return "Creado: " + m[1];'),
        ('^Deleting\\s+(.+)$', 'return "Eliminando " + m[1];'),
        ('^Deleted\\s+(.+)$', 'return "Eliminado: " + m[1];'),
        ('^Analyzing\\s+(.+)$', 'return "Analizando " + m[1];'),
        ('^Analyzed\\s+(.+)$', 'return "Analizado: " + m[1];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Pensó durante " + m[1] + " s" + m[2];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Pensó durante " + m[1] + " min" + m[2];'),
        ('^Thinking for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Pensando " + m[1] + " s" + m[2];'),
        ('^Worked for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Trabajó durante " + m[1] + " s" + m[2];'),
        ('^Step\\s+(\\d+)\\s+of\\s+(\\d+)$', 'return "Paso " + m[1] + " de " + m[2];'),
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "Líneas añadidas: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "Líneas eliminadas: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "Líneas modificadas: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*changed$', 'return "Archivos modificados: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*created$', 'return "Archivos creados: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*deleted$', 'return "Archivos eliminados: " + m[1];'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return "Agentes activos: " + m[1];'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " de " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " elementos";'),
        ('^([0-9]+)\\s+results?$', 'return m[1] + " resultados";'),
    ],
    "ja": [
        ('^Searching for\\s+(.+)$', 'return m[1] + " を検索中";'),
        ('^Searched for\\s+(.+)$', 'return m[1] + " の検索完了";'),
        ('^Reading\\s+(.+)$', 'return m[1] + " を読み込み中";'),
        ('^Read\\s+(.+)$', 'return m[1] + " を読み込み完了";'),
        ('^Editing\\s+(.+)$', 'return m[1] + " を編集中";'),
        ('^Edited\\s+(.+)$', 'return m[1] + " の編集完了";'),
        ('^Running\\s+(.+)$', 'return m[1] + " を実行中";'),
        ('^Ran\\s+(.+)$', 'return m[1] + " を実行完了";'),
        ('^Executing\\s+(.+)$', 'return m[1] + " を実行中";'),
        ('^Executed\\s+(.+)$', 'return m[1] + " の実行完了";'),
        ('^Creating\\s+(.+)$', 'return m[1] + " を作成中";'),
        ('^Created\\s+(.+)$', 'return m[1] + " を作成完了";'),
        ('^Deleting\\s+(.+)$', 'return m[1] + " を削除中";'),
        ('^Deleted\\s+(.+)$', 'return m[1] + " を削除完了";'),
        ('^Analyzing\\s+(.+)$', 'return m[1] + " を分析中";'),
        ('^Analyzed\\s+(.+)$', 'return m[1] + " の分析完了";'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return m[1] + " 秒間思考" + m[2];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return m[1] + " 分間思考" + m[2];'),
        ('^Thinking for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return m[1] + " 秒間思考中" + m[2];'),
        ('^Worked for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return m[1] + " 秒間処理" + m[2];'),
        ('^Step\\s+(\\d+)\\s+of\\s+(\\d+)$', 'return "ステップ " + m[1] + " / " + m[2];'),
        ('^([0-9]+)\\s*lines?\\s*added$', 'return m[1] + " 行追加";'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return m[1] + " 行削除";'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return m[1] + " 行変更";'),
        ('^([0-9]+)\\s*files?\\s*changed$', 'return m[1] + " 件の変更されたファイル";'),
        ('^([0-9]+)\\s*files?\\s*created$', 'return m[1] + " 件の新規作成ファイル";'),
        ('^([0-9]+)\\s*files?\\s*deleted$', 'return m[1] + " 件の削除されたファイル";'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return m[1] + " 件のエージェントが実行中";'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " / " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " 件";'),
        ('^([0-9]+)\\s+results?$', 'return m[1] + " 件の結果";'),
    ],
    "de": [
        ('^Searching for\\s+(.+)$', 'return "Suche nach " + m[1];'),
        ('^Searched for\\s+(.+)$', 'return "Suche abgeschlossen: " + m[1];'),
        ('^Reading\\s+(.+)$', 'return "Lese " + m[1];'),
        ('^Read\\s+(.+)$', 'return "Gelesen: " + m[1];'),
        ('^Editing\\s+(.+)$', 'return "Bearbeite " + m[1];'),
        ('^Edited\\s+(.+)$', 'return "Bearbeitet: " + m[1];'),
        ('^Running\\s+(.+)$', 'return "Führe aus: " + m[1];'),
        ('^Ran\\s+(.+)$', 'return "Ausgeführt: " + m[1];'),
        ('^Executing\\s+(.+)$', 'return "Führe aus: " + m[1];'),
        ('^Executed\\s+(.+)$', 'return "Ausgeführt: " + m[1];'),
        ('^Creating\\s+(.+)$', 'return "Erstelle " + m[1];'),
        ('^Created\\s+(.+)$', 'return "Erstellt: " + m[1];'),
        ('^Deleting\\s+(.+)$', 'return "Lösche " + m[1];'),
        ('^Deleted\\s+(.+)$', 'return "Gelöscht: " + m[1];'),
        ('^Analyzing\\s+(.+)$', 'return "Analysiere " + m[1];'),
        ('^Analyzed\\s+(.+)$', 'return "Analysiert: " + m[1];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Gedacht für " + m[1] + " Sek." + m[2];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Gedacht für " + m[1] + " Min." + m[2];'),
        ('^Thinking for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Denkt seit " + m[1] + " Sek." + m[2];'),
        ('^Step\\s+(\\d+)\\s+of\\s+(\\d+)$', 'return "Schritt " + m[1] + " von " + m[2];'),
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "Zeilen hinzugefügt: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "Zeilen entfernt: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "Zeilen geändert: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*changed$', 'return "Geänderte Dateien: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*created$', 'return "Erstellte Dateien: " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*deleted$', 'return "Gelöschte Dateien: " + m[1];'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return "Aktive Agenten: " + m[1];'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " von " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " Elemente";'),
    ],
    "fr": [
        ('^Searching for\\s+(.+)$', 'return "Recherche de " + m[1];'),
        ('^Searched for\\s+(.+)$', 'return "Recherche terminée : " + m[1];'),
        ('^Reading\\s+(.+)$', 'return "Lecture de " + m[1];'),
        ('^Read\\s+(.+)$', 'return "Lu : " + m[1];'),
        ('^Editing\\s+(.+)$', 'return "Modification de " + m[1];'),
        ('^Edited\\s+(.+)$', 'return "Modifié : " + m[1];'),
        ('^Running\\s+(.+)$', 'return "Exécution de " + m[1];'),
        ('^Ran\\s+(.+)$', 'return "Exécuté : " + m[1];'),
        ('^Executing\\s+(.+)$', 'return "Exécution de " + m[1];'),
        ('^Executed\\s+(.+)$', 'return "Exécuté : " + m[1];'),
        ('^Creating\\s+(.+)$', 'return "Création de " + m[1];'),
        ('^Created\\s+(.+)$', 'return "Créé : " + m[1];'),
        ('^Deleting\\s+(.+)$', 'return "Suppression de " + m[1];'),
        ('^Deleted\\s+(.+)$', 'return "Supprimé : " + m[1];'),
        ('^Analyzing\\s+(.+)$', 'return "Analyse de " + m[1];'),
        ('^Analyzed\\s+(.+)$', 'return "Analysé : " + m[1];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Réfléchi pendant " + m[1] + " s" + m[2];'),
        ('^Thought for\\s+([\\d.]+)\\s*(?:m|minutes?)(.*)$', 'return "Réfléchi pendant " + m[1] + " min" + m[2];'),
        ('^Thinking for\\s+([\\d.]+)\\s*(?:s|seconds?)(.*)$', 'return "Réfléchit pendant " + m[1] + " s" + m[2];'),
        ('^Step\\s+(\\d+)\\s+of\\s+(\\d+)$', 'return "Étape " + m[1] + " sur " + m[2];'),
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "Lignes ajoutées : " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "Lignes supprimées : " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "Lignes modifiées : " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*changed$', 'return "Fichiers modifiés : " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*created$', 'return "Fichiers créés : " + m[1];'),
        ('^([0-9]+)\\s*files?\\s*deleted$', 'return "Fichiers supprimés : " + m[1];'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return "Agents actifs : " + m[1];'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " sur " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " éléments";'),
    ],
}


def get_language_metadata(lang_code: str) -> dict:
    meta_path = LANG_ROOT / lang_code / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "code": lang_code,
        "name": lang_code.upper(),
        "nativeName": lang_code.upper(),
        "version": "1.0.0",
        "translatorTarget": lang_code,
        "flag": "🌐",
        "buttonLabel": f"🌐 {lang_code.upper()}",
        "buttonTitle": f"Translate thoughts to {lang_code}",
        "autoLabelOn": "⚡ Auto: ON",
        "autoLabelOff": "⚡ Auto: OFF",
        "autoTitle": "Auto translate thoughts",
        "originalButton": "🌐 EN",
        "originalTitle": "Show original English text",
        "vscodeLocale": lang_code,
    }


def get_language_dictionary(lang_code: str) -> dict:
    dict_path = LANG_ROOT / lang_code / "dict.json"
    if dict_path.exists():
        with open(dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_runtime_translator_js(lang_code: str = "ru") -> str:
    meta = get_language_metadata(lang_code)
    dictionary = get_language_dictionary(lang_code)

    target_lang = meta.get("translatorTarget", lang_code)
    btn_label = meta.get("buttonLabel", f"🌐 {lang_code.upper()}")
    btn_title = meta.get("buttonTitle", f"Translate thoughts to {meta.get('nativeName', lang_code)}")
    auto_on = meta.get("autoLabelOn", "⚡ Auto: ON")
    auto_off = meta.get("autoLabelOff", "⚡ Auto: OFF")
    auto_title = meta.get("autoTitle", "Auto translate thoughts")
    orig_btn = meta.get("originalButton", "🌐 EN")
    orig_title = meta.get("originalTitle", "Show original English text")

    rules = RULE_TEMPLATES.get(lang_code, RULE_TEMPLATES.get("en", [
        ('^([0-9]+)\\s*lines?\\s*added$', 'return m[1] + " lines added";'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return m[1] + " lines removed";'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " of " + m[2];'),
    ]))

    rules_js_lines = []
    for pattern, repl in rules:
        rules_js_lines.append(f"""    {{
      regex: /{pattern}/i,
      replace: function (m) {{ {repl} }}
    }}""")
    rules_js_str = ",\n".join(rules_js_lines)

    dict_json = json.dumps(dictionary, ensure_ascii=False, indent=2)
    thought_engine = (REPO_ROOT / "translations" / "structured_thoughts.js").read_text(encoding="utf-8")

    js_code = f"""{PRELOAD_MARKER}
/**
 * Dagami Antigravity Language Pack — {meta.get('name', lang_code)} ({meta.get('nativeName', lang_code)})
 * Telegram: https://t.me/+8qU7020rMF84OWNi
 * Donation: https://pay.cloudtips.ru/p/671fda86
 */
(function () {{
  'use strict';

  const TARGET_LANG = {json.dumps(target_lang)};
  const BUTTON_LABEL = {json.dumps(btn_label)};
  const BUTTON_TITLE = {json.dumps(btn_title)};
  const AUTO_LABEL_ON = {json.dumps(auto_on)};
  const AUTO_LABEL_OFF = {json.dumps(auto_off)};
  const AUTO_TITLE = {json.dumps(auto_title)};
  const ORIG_BUTTON = {json.dumps(orig_btn)};
  const ORIG_TITLE = {json.dumps(orig_title)};

  const DICT = {dict_json};

  const RULES = [
{rules_js_str}
  ];

  const IGNORE_TAGS = new Set([
    'SCRIPT', 'STYLE', 'CODE', 'PRE', 'TEXTAREA', 'INPUT'
  ]);

  function isIgnored(node) {{
    if (!node) return true;
    let el = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    while (el) {{
      if (el.matches && el.matches('[data-testid="thinking-collapsible-content"],.markdown-body,.rendered-markdown,.cursor-edit')) return true;
      if (IGNORE_TAGS.has(el.tagName)) return true;
      if (el.classList) {{
        if (
          el.classList.contains('token') ||
          el.classList.contains('prism') ||
          el.classList.contains('monaco-editor') ||
          el.classList.contains('cm-editor') ||
          el.classList.contains('xterm') ||
          el.classList.contains('ag-thought-toolbar') ||
          el.classList.contains('ag-thought-overlay') ||
          el.classList.contains('notranslate')
        ) {{
          return true;
        }}
      }}
      if (el.getAttribute && el.getAttribute('data-notranslate') !== null) {{
        return true;
      }}
      el = el.parentElement;
    }}
    return false;
  }}

  function translateString(text) {{
    if (typeof text !== 'string') return null;
    const trimmed = text.trim();
    if (!trimmed) return null;

    const startSpace = text.match(/^\\s*/)[0];
    const endSpace = text.match(/\\s*$/)[0];

    // 1. Direct dictionary lookup
    if (DICT[trimmed]) {{
      return startSpace + DICT[trimmed] + endSpace;
    }}

    // 2. Dynamic regex rules
    for (let i = 0; i < RULES.length; i++) {{
      const match = trimmed.match(RULES[i].regex);
      if (match) {{
        return startSpace + RULES[i].replace(match) + endSpace;
      }}
    }}

    // 3. Prefix matching: "Prefix: Value"
    const pfxMatch = trimmed.match(/^([A-Za-z0-9 ]+:)\\s*(.+)$/);
    if (pfxMatch && DICT[pfxMatch[1]]) {{
      const pfxTrans = DICT[pfxMatch[1]];
      const val = pfxMatch[2].trim();
      const valTrans = DICT[val] || val;
      return startSpace + pfxTrans + ' ' + valTrans + endSpace;
    }}

    return null;
  }}

  function translateNode(node) {{
    if (!node) return;
    if (node.nodeType === Node.TEXT_NODE) {{
      if (isIgnored(node)) return;
      const translated = translateString(node.nodeValue);
      if (translated && translated !== node.nodeValue) {{
        node.nodeValue = translated;
      }}
    }} else if (node.nodeType === Node.ELEMENT_NODE) {{
      if (isIgnored(node)) return;

      if (node.hasAttribute('placeholder')) {{
        const trans = translateString(node.getAttribute('placeholder'));
        if (trans && trans !== node.getAttribute('placeholder')) node.setAttribute('placeholder', trans);
      }}
      if (node.hasAttribute('title')) {{
        const trans = translateString(node.getAttribute('title'));
        if (trans && trans !== node.getAttribute('title')) node.setAttribute('title', trans);
      }}
      if (node.hasAttribute('aria-label')) {{
        const trans = translateString(node.getAttribute('aria-label'));
        if (trans && trans !== node.getAttribute('aria-label')) node.setAttribute('aria-label', trans);
      }}

      for (let child = node.firstChild; child; child = child.nextSibling) {{
        translateNode(child);
      }}
    }}
  }}

  try {{
    const origNodeValueDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'nodeValue');
    if (origNodeValueDesc && origNodeValueDesc.set) {{
      const origSet = origNodeValueDesc.set;
      Object.defineProperty(Node.prototype, 'nodeValue', {{
        get: origNodeValueDesc.get,
        set: function (val) {{
          if (this.nodeType === Node.TEXT_NODE && typeof val === 'string' && !isIgnored(this)) {{
            const trans = translateString(val);
            if (trans) val = trans;
          }}
          return origSet.call(this, val);
        }},
        configurable: true,
        enumerable: true
      }});
    }}

    const origTextContentDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
    if (origTextContentDesc && origTextContentDesc.set) {{
      const origTextSet = origTextContentDesc.set;
      Object.defineProperty(Node.prototype, 'textContent', {{
        get: origTextContentDesc.get,
        set: function (val) {{
          if (typeof val === 'string' && !isIgnored(this)) {{
            const trans = translateString(val);
            if (trans) val = trans;
          }}
          return origTextSet.call(this, val);
        }},
        configurable: true,
        enumerable: true
      }});
    }}
  }} catch (e) {{
    console.warn('[DagamiLang] Hook setup error:', e);
  }}

  function startObserver() {{
    const observer = new MutationObserver((mutations) => {{
      for (let i = 0; i < mutations.length; i++) {{
        const m = mutations[i];
        if (m.type === 'childList') {{
          for (let j = 0; j < m.addedNodes.length; j++) {{
            translateNode(m.addedNodes[j]);
          }}
        }} else if (m.type === 'characterData') {{
          translateNode(m.target);
        }} else if (m.type === 'attributes') {{
          if (isIgnored(m.target)) continue;
          if (['placeholder', 'title', 'aria-label'].includes(m.attributeName)) {{
            const val = m.target.getAttribute(m.attributeName);
            const trans = translateString(val);
            if (trans && trans !== val) {{
              m.target.setAttribute(m.attributeName, trans);
            }}
          }}
        }}
      }}
    }});

    observer.observe(document.documentElement, {{
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['placeholder', 'title', 'aria-label']
    }});

    translateNode(document.body || document.documentElement);
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', startObserver);
  }} else {{
    startObserver();
  }}

  {thought_engine}
  StructuredThoughts.install({{
    target: TARGET_LANG, button: BUTTON_LABEL, buttonTitle: BUTTON_TITLE,
    autoOn: AUTO_LABEL_ON, autoOff: AUTO_LABEL_OFF, autoTitle: AUTO_TITLE,
    originalButton: ORIG_BUTTON, originalTitle: ORIG_TITLE,
    cancelTitle: {json.dumps({'ru':'Отмена','zh':'取消','es':'Cancelar','ja':'キャンセル','de':'Abbrechen','fr':'Annuler'}.get(lang_code,'Cancel'))},
    errorTitle: {json.dumps({'ru':'Сбой перевода. Повторите позже.','zh':'翻译失败，请重试。','es':'Error al traducir. Reintenta.','ja':'翻訳に失敗しました。再試行してください。','de':'Fehler. Bitte erneut versuchen.','fr':'Echec. Veuillez reessayer.'}.get(lang_code,'Could not translate. Try again.'))}
  }});

  console.log('[DagamiLang] ' + {json.dumps(meta.get('name', lang_code))} + ' pack active with ' + Object.keys(DICT).length + ' strings');
}})();
"""
    return js_code
