"""
Утилиты для безопасного чтения, изменения и валидации JSONC (JSON with Comments).

Поддерживает:
- Однострочные (//) и многострочные (/* */) комментарии;
- Допустимые в JSONC завершающие запятые (trailing commas);
- Добавление настроек в пустые объекты ({}) без создания недопустимых запятых;
- Замену только активных настроек (игнорируя закомментированные ключи);
- Атомарную запись и сквозную пост-валидацию.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Optional

from js_literals import tokenize_javascript


def strip_jsonc(text: str) -> str:
    """
    Удаляет комментарии и нормализует завершающие запятые перед закрывающими скобками,
    делая строку пригодной для стандартного json.loads.
    """
    def replacer(match: re.Match) -> str:
        s = match.group(0)
        if s.startswith("/"):
            return ""
        return s

    # 1. Удаляем комментарии, сохраняя строковые литералы
    comment_pattern = re.compile(r'//.*?$|/\*.*?\*/|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE)
    no_comments = re.sub(comment_pattern, replacer, text)

    # 2. Удаляем завершающие запятые перед } или ] (trailing commas, допустимые в JSONC)
    trailing_comma_pattern = re.compile(r',\s*([\]}])')
    clean = re.sub(trailing_comma_pattern, r'\1', no_comments)
    return clean


def parse_jsonc(text: str) -> Any:
    """
    Парсит строку в формате JSONC в Python-объект.
    """
    clean = strip_jsonc(text)
    return json.loads(clean)


def update_argv_locale(
    argv_path: Path,
    target_locale: str = "ru",
    log_fn: Optional[Callable[[str], None]] = None,
) -> bool:
    """
    Устанавливает locale в argv.json.

    Гарантии:
      - Если файл отсутствует, создается валидный JSON {"locale": target_locale};
      - Если в файле {}, создается валидный объект без завершающей запятой;
      - Закомментированные // "locale": "..." НЕ принимаются за активные;
      - Если активный locale уже установлен в target_locale, сообщает ALREADY_DONE;
      - Существующие комментарии и форматирование сохраняются;
      - Пост-валидация проверяет фактическое значение locale после записи на диск.
    """
    logger = log_fn or (lambda m: None)

    # 1. Если файла нет — создаем его с нуля
    if not argv_path.exists():
        try:
            argv_path.parent.mkdir(parents=True, exist_ok=True)
            initial_content = f'{{\n\t"locale": "{target_locale}"\n}}\n'
            _atomic_write(argv_path, initial_content)
            # Проверка
            with open(argv_path, "r", encoding="utf-8") as f:
                data = parse_jsonc(f.read())
            if data.get("locale") == target_locale:
                logger(f"  [argv.json] Файл создан с параметром locale: {target_locale}")
                return True
        except Exception as e:
            logger(f"  [argv.json] Ошибка создания файла: {e}")
            return False

    try:
        with open(argv_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Парсим текущие активные настройки
        current_data = parse_jsonc(original_content) if original_content.strip() else {}
        if not isinstance(current_data, dict):
            current_data = {}

        if current_data.get("locale") == target_locale:
            logger(f"  [argv.json] Параметр locale уже установлен в '{target_locale}'.")
            return True

        tokens = tokenize_javascript(original_content)
        sig_tokens = [t for t in tokens if t.type != "COMMENT"]

        # Ищем активный ключ "locale"
        active_locale_token_idx = None
        for i, t in enumerate(sig_tokens):
            if t.type == "STRING" and t.value == "locale":
                if i + 1 < len(sig_tokens) and sig_tokens[i + 1].value == ":":
                    active_locale_token_idx = i
                    break

        new_content = original_content

        if active_locale_token_idx is not None:
            # Активный ключ существует — заменяем значение
            val_token = sig_tokens[active_locale_token_idx + 2]
            if val_token.type == "STRING" and val_token.quote:
                start = val_token.start
                end = val_token.end
                q = val_token.quote
                new_chunk = f"{q}{target_locale}{q}"
                new_content = original_content[:start] + new_chunk + original_content[end:]
        else:
            # Ключа нет — внедряем в корневой объект
            # Ищем первый открывающий {
            first_brace_idx = None
            for idx, t in enumerate(sig_tokens):
                if t.type == "PUNCT" and t.value == "{":
                    first_brace_idx = idx
                    break

            if first_brace_idx is None:
                new_content = f'{{\n\t"locale": "{target_locale}"\n}}\n'
            else:
                brace_token = sig_tokens[first_brace_idx]
                next_sig = sig_tokens[first_brace_idx + 1] if first_brace_idx + 1 < len(sig_tokens) else None

                insert_pos = brace_token.end
                if next_sig and next_sig.type == "PUNCT" and next_sig.value == "}":
                    # Пустой объект {} -> вставляем без завершающей запятой
                    indent = "\n\t"
                    insert_text = f'{indent}"locale": "{target_locale}"\n'
                    # Если между { и } были только пробелы, заменяем их
                    new_content = (
                        original_content[:insert_pos]
                        + insert_text
                        + original_content[next_sig.start:]
                    )
                else:
                    # Непустой объект -> вставляем с запятой
                    insert_text = f'\n\t"locale": "{target_locale}",'
                    new_content = (
                        original_content[:insert_pos]
                        + insert_text
                        + original_content[insert_pos:]
                    )

        # Предварительная валидация
        post_data = parse_jsonc(new_content)
        if post_data.get("locale") != target_locale:
            raise ValueError(f"Валидация JSONC не подтвердила locale={target_locale}")

        # Атомарная запись на диск
        _atomic_write(argv_path, new_content)

        # Пост-валидация с диска
        with open(argv_path, "r", encoding="utf-8") as f:
            disk_data = parse_jsonc(f.read())
        if disk_data.get("locale") != target_locale:
            raise ValueError(f"Пост-валидация с диска не подтвердила locale={target_locale}")

        logger(f"  [argv.json] Успешно установлен locale: {target_locale}")
        return True

    except Exception as e:
        logger(f"  [argv.json] Ошибка обновления/валидации: {e}")
        return False


def _atomic_write(path: Path, content: str) -> None:
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
