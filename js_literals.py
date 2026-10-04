"""
Общие примитивы замены строковых литералов в JS-коде.

Модуль выполняет контекстно-зависимую и синтаксически безопасную замену
строковых литералов пользовательского интерфейса (UI) без повреждения машинных значений:
- Ключи объектов ({"prop": 1}) и вычисляемые свойства ({[prop]: 1}) не заменяются;
- Обращения к свойствам через скобки (obj["prop"], obj?.["prop"]) не заменяются;
- Модульные спецификаторы (import ... from "...", require("...")) не заменяются;
- Содержимое комментариев (//, /* */) защищено от подмены;
- Экранирование строковых и template literals сохраняется байт-в-байт.

Реализация использует детерминированный синтаксический токенизатор на базе стандартной
библиотеки Python для соблюдения принципа «zero-dependency offline install».
"""

from __future__ import annotations

import re
from typing import Callable, NamedTuple, Optional

__all__ = [
    "BLACKLIST_PATTERNS",
    "escape_js_string",
    "is_system_identifier",
    "build_literal_pattern",
    "replace_js_string_literals",
]

BLACKLIST_PATTERNS = (
    "vscode.", "antigravity.", "http://", "https://", "file://",
    ".js", ".json", ".ts", ".node", "/", "\\",
)

JS_KEYWORDS = {
    "break", "case", "catch", "class", "const", "continue", "debugger",
    "default", "delete", "do", "else", "export", "extends", "finally",
    "for", "function", "if", "import", "in", "instanceof", "new",
    "return", "super", "switch", "this", "throw", "try", "typeof",
    "var", "void", "while", "with", "yield", "let", "static", "await",
    "from", "as",
}


def is_system_identifier(text: str) -> bool:
    """
    True, если строка похожа на системный идентификатор, а не на UI-текст.
    """
    if not text:
        return False
    looks_like_ui_text = (" " in text) or text.endswith(":") or text.endswith(".")
    if looks_like_ui_text:
        return False
    return any(bp in text for bp in BLACKLIST_PATTERNS)


def escape_js_string(text: str, quote: str) -> str:
    """
    Экранирует текст так, чтобы он был безопасен внутри JS-литерала с данной кавычкой.
    """
    if quote not in ("'", '"', "`"):
        raise ValueError(f"unsupported quote: {quote!r}")

    out = text.replace("\\", "\\\\")
    out = out.replace(quote, "\\" + quote)
    if quote == "`":
        out = out.replace("${", "\\${")
    out = out.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return out


def build_literal_pattern(text: str) -> re.Pattern[str]:
    """
    Компилирует регулярное выражение для поиска строкового литерала.
    Сохранено для обратной совместимости вызовов.
    """
    return re.compile(
        r'(?<![a-zA-Z0-9_$\.\:])(["\'`])' + re.escape(text) + r'\1(?!\s*:)'
    )


class JsToken(NamedTuple):
    type: str
    value: str
    raw: str
    start: int
    end: int
    quote: Optional[str] = None


def tokenize_javascript(source: str) -> list[JsToken]:
    """
    Линейный токенизатор JavaScript / TypeScript кода.
    Точно разделяет комментарии, строковые литералы, регулярные выражения,
    идентификаторы и пунктуацию.
    """
    tokens: list[JsToken] = []
    i = 0
    n = len(source)

    while i < n:
        c = source[i]

        # 1. Пробелы
        if c in " \t\r\n":
            i += 1
            continue

        # 2. Комментарии
        if c == "/" and i + 1 < n:
            c2 = source[i + 1]
            if c2 == "/":
                start = i
                i += 2
                while i < n and source[i] != "\n":
                    i += 1
                tokens.append(JsToken("COMMENT", source[start:i], source[start:i], start, i))
                continue
            elif c2 == "*":
                start = i
                i += 2
                while i + 1 < n and not (source[i] == "*" and source[i + 1] == "/"):
                    i += 1
                if i + 1 < n:
                    i += 2
                else:
                    i = n
                tokens.append(JsToken("COMMENT", source[start:i], source[start:i], start, i))
                continue

        # 3. Строковые литералы
        if c in ('"', "'", "`"):
            quote = c
            start = i
            i += 1
            val_chars: list[str] = []
            while i < n:
                ch = source[i]
                if ch == "\\":
                    if i + 1 < n:
                        next_ch = source[i + 1]
                        if next_ch == quote:
                            val_chars.append(quote)
                        elif next_ch == "\\":
                            val_chars.append("\\")
                        elif next_ch == "n":
                            val_chars.append("\n")
                        elif next_ch == "r":
                            val_chars.append("\r")
                        elif next_ch == "t":
                            val_chars.append("\t")
                        else:
                            val_chars.append("\\" + next_ch)
                        i += 2
                        continue
                    else:
                        val_chars.append("\\")
                        i += 1
                        break
                elif ch == quote:
                    i += 1
                    break
                elif quote == "`" and ch == "$" and i + 1 < n and source[i + 1] == "{":
                    val_chars.append("${")
                    i += 2
                    depth = 1
                    while i < n and depth > 0:
                        if source[i] == "{":
                            depth += 1
                        elif source[i] == "}":
                            depth -= 1
                        val_chars.append(source[i])
                        i += 1
                    continue
                else:
                    val_chars.append(ch)
                    i += 1

            raw = source[start:i]
            val = "".join(val_chars)
            tokens.append(JsToken("STRING", val, raw, start, i, quote=quote))
            continue

        # 4. Регулярные выражения vs деление
        if c == "/":
            prev_sig = None
            for prev in reversed(tokens):
                if prev.type != "COMMENT":
                    prev_sig = prev
                    break

            is_regex = False
            if prev_sig is None:
                is_regex = True
            elif prev_sig.type == "PUNCT" and prev_sig.value in (
                "(", "[", "{", ";", ",", "=", ":", "?", "!", "&", "|", "^", "~", "+", "-", "*", "%", "<", ">"
            ):
                is_regex = True
            elif prev_sig.type == "KEYWORD" and prev_sig.value in (
                "return", "case", "throw", "yield", "await", "typeof", "void", "delete"
            ):
                is_regex = True

            if is_regex:
                start = i
                i += 1
                in_class = False
                while i < n:
                    ch = source[i]
                    if ch == "\\" and i + 1 < n:
                        i += 2
                    elif ch == "[":
                        in_class = True
                        i += 1
                    elif ch == "]" and in_class:
                        in_class = False
                        i += 1
                    elif ch == "/" and not in_class:
                        i += 1
                        while i < n and source[i].isalpha():
                            i += 1
                        break
                    elif ch == "\n":
                        break
                    else:
                        i += 1
                tokens.append(JsToken("REGEXP", source[start:i], source[start:i], start, i))
                continue
            else:
                start = i
                if i + 1 < n and source[i + 1] == "=":
                    i += 2
                    tokens.append(JsToken("PUNCT", "/=", "/=", start, i))
                else:
                    i += 1
                    tokens.append(JsToken("PUNCT", "/", "/", start, i))
                continue

        # 5. Опциональная цепочка ?.
        if c == "?" and i + 1 < n and source[i + 1] == ".":
            if i + 2 < n and source[i + 2].isdigit():
                tokens.append(JsToken("PUNCT", "?", "?", i, i + 1))
                i += 1
            else:
                tokens.append(JsToken("PUNCT", "?.", "?.", i, i + 2))
                i += 2
            continue

        # 6. Многосимвольные операторы
        two_char = source[i:i + 2]
        if two_char in ("=>", "==", "!=", "<=", ">=", "&&", "||", "??", "++", "--", "<<", ">>", "+=", "-=", "*="):
            tokens.append(JsToken("PUNCT", two_char, two_char, i, i + 2))
            i += 2
            continue

        # 7. Базовая пунктуация
        if c in "()[]{},;:?~!&|^+-*%=<>":
            tokens.append(JsToken("PUNCT", c, c, i, i + 1))
            i += 1
            continue

        if c == ".":
            tokens.append(JsToken("PUNCT", ".", ".", i, i + 1))
            i += 1
            continue

        # 8. Идентификаторы / ключевые слова / числа
        start = i
        while i < n and (source[i].isalnum() or source[i] in "_$"):
            i += 1
        word = source[start:i]
        if word:
            if word in JS_KEYWORDS:
                tokens.append(JsToken("KEYWORD", word, word, start, i))
            elif word[0].isdigit():
                tokens.append(JsToken("NUMBER", word, word, start, i))
            else:
                tokens.append(JsToken("IDENT", word, word, start, i))
            continue

        # 9. Прочие символы
        tokens.append(JsToken("OTHER", c, c, i, i + 1))
        i += 1

    return tokens


def replace_js_string_literals(
    content: str,
    string_map: dict[str, str],
    log_fn: Optional[Callable[[str], None]] = None,
) -> tuple[str, int]:
    """
    Контекстно-зависимая замена строковых литералов в JS-коде.

    Возвращает (новое_содержимое, число_замен). Не мутирует вход.

    Безопасность:
      - Проверяет синтаксический контекст каждого строкового литерала через AST-токены;
      - Не заменяет обращения к свойствам (obj["key"], obj?.["key"]);
      - Не заменяет ключи объектов ({"key": val}) и вычисляемые свойства ({[key]: val});
      - Не заменяет импорты (import ... from "...") и вызовы require("...");
      - Игнорирует комментарии;
      - Экранирует спецсимволы в соответствии с типом кавычек.
    """
    if not content or not string_map:
        return content, 0

    tokens = tokenize_javascript(content)
    sig_indices = [idx for idx, t in enumerate(tokens) if t.type != "COMMENT"]

    replacements: list[tuple[int, int, str]] = []

    for sig_pos, tok_idx in enumerate(sig_indices):
        tok = tokens[tok_idx]
        if tok.type != "STRING" or not tok.quote:
            continue

        source_val = tok.value
        if source_val not in string_map:
            continue

        target_val = string_map[source_val]
        if not isinstance(target_val, str):
            if log_fn:
                log_fn(f"  [Пропуск] Нестроковый перевод для '{source_val}': {type(target_val).__name__}")
            continue
        if not target_val or source_val == target_val:
            continue

        if is_system_identifier(source_val):
            if log_fn:
                log_fn(f"  [Контекстный фильтр] Пропуск системного идентификатора: '{source_val}'")
            continue

        # Проверка предшествующего синтаксического контекста
        prev1 = tokens[sig_indices[sig_pos - 1]] if sig_pos > 0 else None
        prev2 = tokens[sig_indices[sig_pos - 2]] if sig_pos > 1 else None

        # 1. Модульные спецификаторы: import / from / require
        if prev1 and prev1.value in ("from", "import"):
            continue
        if prev1 and prev1.value == "(" and prev2 and prev2.value in ("require", "import"):
            continue

        # 2. Обращение к свойствам: obj.prop, obj?.prop
        if prev1 and prev1.value in (".", "?."):
            continue

        # 3. Индексатор / обращение по скобкам: obj["prop"], obj?.["prop"], arr[0]["prop"]
        if prev1 and prev1.value == "[":
            if prev2 and (
                prev2.type in ("IDENT", "NUMBER")
                or prev2.value in (")", "]", "}", "?.")
            ):
                if log_fn:
                    log_fn(f"  [Синтаксическая защита] Пропуск обращения к свойству: '{source_val}'")
                continue

        # Проверка последующего синтаксического контекста
        next1 = tokens[sig_indices[sig_pos + 1]] if sig_pos + 1 < len(sig_indices) else None
        next2 = tokens[sig_indices[sig_pos + 2]] if sig_pos + 2 < len(sig_indices) else None

        # 4. Ключ объекта: "key": val
        if next1 and next1.value == ":":
            if log_fn:
                log_fn(f"  [Синтаксическая защита] Пропуск ключа объекта: '{source_val}'")
            continue

        # 5. Вычисляемый ключ объекта: { ["key"]: val }
        if next1 and next1.value == "]" and next2 and next2.value == ":":
            if log_fn:
                log_fn(f"  [Синтаксическая защита] Пропуск вычисляемого ключа объекта: '{source_val}'")
            continue

        # 6. Ключевые слова as
        if next1 and next1.value == "as":
            continue

        # Формирование безопасной экранированной замены
        escaped_replacement = escape_js_string(target_val, tok.quote)
        new_literal = f"{tok.quote}{escaped_replacement}{tok.quote}"
        replacements.append((tok.start, tok.end, new_literal))

    if not replacements:
        return content, 0

    # Применяем замены в обратном порядке (с конца файла), сохраняя целостность смещений
    replacements.sort(key=lambda r: r[0], reverse=True)
    chars = list(content)
    for start, end, new_chunk in replacements:
        chars[start:end] = list(new_chunk)

    result = "".join(chars)
    return result, len(replacements)
