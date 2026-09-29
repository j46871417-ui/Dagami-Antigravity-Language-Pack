"""
Общие примитивы замены строковых литералов в JS-коде.

Модуль существует потому, что до него одну и ту же задачу решали три разные
реализации (patch_ide.patch_extension_js, antigravity_localizer.replace_js_string_literals
и сырой str.replace в Program.cs), и все три расходились в экранировании.
Здесь — единственная авторитетная версия; остальные должны её переиспользовать.

Зависимостей нет (только стандартная библиотека), чтобы соответствовать
требованию «zero-dependency offline install».
"""

from __future__ import annotations

import re

__all__ = [
    "BLACKLIST_PATTERNS",
    "escape_js_string",
    "is_system_identifier",
    "build_literal_pattern",
    "replace_js_string_literals",
]

# Служебные идентификаторы, протоколы, расширения и системные пути.
# Строки, содержащие их, не переводятся, если не похожи на обычный UI-текст.
BLACKLIST_PATTERNS = (
    "vscode.", "antigravity.", "http://", "https://", "file://",
    ".js", ".json", ".ts", ".node", "/", "\\",
)


def is_system_identifier(text: str) -> bool:
    """
    True, если строка похожа на системный идентификатор, а не на UI-текст.

    Эвристика унаследована из antigravity_localizer.replace_js_string_literals:
    строка с точкой/слэшем/расширением файла пропускается, НО только если она не
    содержит пробела и не похожа на предложение/метку. Иначе терялись бы
    легитимные подписи вида "Open in Browser…" или "Save as .txt".
    """
    if not text:
        return False
    looks_like_ui_text = (" " in text) or text.endswith(":") or text.endswith(".")
    if looks_like_ui_text:
        return False
    return any(bp in text for bp in BLACKLIST_PATTERNS)


def escape_js_string(text: str, quote: str) -> str:
    """
    Экранирует текст так, чтобы он был безопасен внутри JS-литерала с данной
    кавычкой.

    Правила по типам кавычек:
      - ' и "  : экранируем обратный слэш, саму кавычку, переводы строк.
      - `       : экранируем обратный слэш, обратную кавычку, ${ (начало
                  подстановки) и переводы строк.

    Порядок важен: обратный слэш экранируется ПЕРВЫМ, иначе он заэкранирует
    слэши, добавленные последующими заменами.

    Без этой функции перевод, содержащий кавычку (например, «Файл "имя"»),
    давал синтаксически битый JS, а в backtick-литерале выражение ${...}
    исполнялось как код — то есть подстановка из словаря переводов.
    """
    if quote not in ("'", '"', "`"):
        raise ValueError(f"unsupported quote: {quote!r}")

    out = text.replace("\\", "\\\\")
    out = out.replace(quote, "\\" + quote)
    if quote == "`":
        # ${ открывает подстановку в template literal — нейтрализуем.
        out = out.replace("${", "\\${")
    # Переводы строк внутри строкового литерала ломают синтаксис.
    out = out.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return out


def build_literal_pattern(text: str) -> re.Pattern[str]:
    """
    Компилирует шаблон поиска строкового литерала с произвольным типом кавычек.

    Требования к шаблону:
      - кавычка (', " или `) до и та же после — обратная ссылка \\1;
      - слева не должно быть идентификатора/точки/двоеточия, иначе мы попадём
        внутрь другого литерала или в ключ объекта;
      - справа не должно быть двоеточия — это ключ объекта ("prop": val),
        а не значение, и такие ключи переводить нельзя.

    re.escape применяется к ТЕКСТУ, а не к шаблону целиком: именно смешение
    этих ролей было дефектом F-001 (re.escape-строка искалась как литерал).
    """
    return re.compile(
        r'(?<![a-zA-Z0-9_$\.\:])(["\'`])' + re.escape(text) + r'\1(?!\s*:)'
    )


def replace_js_string_literals(
    content: str,
    string_map: dict[str, str],
    log_fn=None,
) -> tuple[str, int]:
    """
    Контекстно-зависимая замена строковых литералов в JS-коде.

    Возвращает (новое_содержимое, число_замен). Не мутирует вход.

    Отличия от прежней реализации:
      - экранирование вынесено в escape_js_string и покрывает backslash,
        backtick и ${ (F-026);
      - одинаково работает для ' " и ` (раньше backtick не экранировался);
      - string_map не мутируется во время итерации.
    """
    changes = 0
    result = content

    for en_s, ru_s in string_map.items():
        if not en_s or not isinstance(en_s, str) or en_s == ru_s:
            continue
        if not isinstance(ru_s, str):
            # Значение словаря не строка — пропускаем, а не роняем установку.
            if log_fn:
                log_fn(f"  [Пропуск] Нестроковый перевод для '{en_s}': {type(ru_s).__name__}")
            continue
        if is_system_identifier(en_s):
            if log_fn:
                log_fn(f"  [Контекстный фильтр] Пропуск потенциального системного идентификатора: '{en_s}'")
            continue

        pattern = build_literal_pattern(en_s)

        def make_repl(quote_match: re.Match[str], _ru: str = ru_s) -> str:
            q = quote_match.group(1)
            return f"{q}{escape_js_string(_ru, q)}{q}"

        new_content, count = pattern.subn(make_repl, result)
        if count > 0:
            result = new_content
            changes += count
        elif en_s in result and log_fn:
            log_fn(
                f"  [Контекстный фильтр] Строка '{en_s}' пропущена: "
                "используется как ключ объекта или имя свойства."
            )

    return result, changes
