/**
 * Регрессионные тесты MarkdownShield (Раздел 6).
 * Проверяет:
 * - Побайтовое сохранение защищаемых фрагментов (блоки кода, 3+ переноса строк, отступы);
 * - Снятие ограничения в 150 символов для инлайн-кода;
 * - Экранирование многострочного инлайн-кода и ссылок;
 * - Устойчивость к коллизиям и уникальные нонсы;
 * - Верификацию целостности маркеров.
 */

import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');
const i18nFile = path.join(repoRoot, 'resources', 'web_bundle_ru', 'i18n-ru.js');

// Извлекаем объявление MarkdownShield из i18n-ru.js
const code = fs.readFileSync(i18nFile, 'utf-8');
const shieldMatch = code.match(/class MarkdownShield[\s\S]*?\n  \}/);
if (!shieldMatch) {
  throw new Error('Не удалось найти MarkdownShield в i18n-ru.js');
}

const context = { console };
vm.createContext(context);
const MarkdownShield = vm.runInContext(`(function() { ${shieldMatch[0]}; return MarkdownShield; })()`, context);

console.log('--- Запуск тестов MarkdownShield ---');

// Тест 1: Побайтовое сохранение блоков кода с 3+ переносами строк и отступами
{
  const shield = new MarkdownShield();
  const rawCodeBlock = "```python\ndef test():\n\n\n\n    # 4 newlines and spaces\n    return 42\n```";
  const source = `Привет!\n\n${rawCodeBlock}\n\nПока!`;

  const masked = shield.mask(source);
  assert(!masked.includes('def test()'), 'Блок кода должен быть замаскирован');

  // Симулируем перевод окружающего текста
  const simulatedTranslated = masked
    .replace('Привет!', 'Hello!')
    .replace('Пока!', 'Goodbye!');

  const unmasked = shield.unmask(simulatedTranslated);
  assert(unmasked.includes(rawCodeBlock), 'Блок кода должен сохраниться байт-в-байт без сжатия строк!');
  console.log('✓ Тест 1 пройден: побайтовое сохранение блоков кода с \\n\\n\\n и отступами');
}

// Тест 2: Снятие ограничения в 150 символов на инлайн-код
{
  const shield = new MarkdownShield();
  const longInlineCode = '`' + 'a'.repeat(300) + '`';
  const source = `Выполните команду: ${longInlineCode}`;

  const masked = shield.mask(source);
  assert(!masked.includes('a'.repeat(300)), 'Длинный инлайн-код (>150 символов) должен быть замаскирован');

  const unmasked = shield.unmask(masked);
  assert.strictEqual(unmasked, source, 'Длинный инлайн-код должен восстанавливаться без потерь');
  console.log('✓ Тест 2 пройден: инлайн-код >150 символов защищается и восстанавливается');
}

// Тест 3: Многострочный инлайн-код
{
  const shield = new MarkdownShield();
  const multilineInline = '`const x = 1;\nconst y = 2;`';
  const source = `Смотрите ${multilineInline} здесь.`;

  const masked = shield.mask(source);
  assert(!masked.includes('const x = 1;'), 'Многострочный инлайн-код должен маскироваться');

  const unmasked = shield.unmask(masked);
  assert.strictEqual(unmasked, source);
  console.log('✓ Тест 3 пройден: многострочный инлайн-код сохраняется');
}

// Тест 4: Защита Markdown URL ссылок
{
  const shield = new MarkdownShield();
  const url = 'https://example.com/api/v1?token=xyz123&scope=all#heading';
  const source = `Документация: [API Docs](${url})`;

  const masked = shield.mask(source);
  assert(!masked.includes(url), 'URL в ссылке должен быть замаскирован');

  const unmasked = shield.unmask(masked);
  assert.strictEqual(unmasked, source, 'URL должен восстановиться без искажений');
  console.log('✓ Тест 4 пройден: защита URL в Markdown-ссылках');
}

// Тест 5: Устойчивость к коллизиям и уникальные нонсы
{
  const shield1 = new MarkdownShield();
  const shield2 = new MarkdownShield();
  assert.notStrictEqual(shield1.nonce, shield2.nonce, 'Разные экземпляры должны иметь разные нонсы');

  // Текст пользователя, случайно содержащий старый/чужой маркер
  const fakeTokenText = 'Текст с токеном ⟦AGB_0⟧ внутри описания.';
  const masked = shield1.mask(fakeTokenText);
  const unmasked = shield1.unmask(masked);
  assert.strictEqual(unmasked, fakeTokenText, 'Пользовательский текст с фейковым маркером не должен ломаться');
  console.log('✓ Тест 5 пройден: уникальные нонсы и защита от коллизий');
}

// Тест 6: Верификация целостности при повреждении маркера переводчиком
{
  const shield = new MarkdownShield();
  const codeBlock = "```json\n{\"safe\": true}\n```";
  const source = `Конфиг:\n${codeBlock}`;

  const masked = shield.mask(source);
  // Имитируем ошибку переводчика: удалил маркер ⟦AGB...⟧
  const damagedTranslation = "Конфиг: (переводчик удалил маркер)";

  const recovered = shield.unmask(damagedTranslation);
  assert(recovered.includes(codeBlock), 'Потерянный блок кода должен быть безопасно возвращен в вывод');
  console.log('✓ Тест 6 пройден: целостность кода при повреждении маркеров');
}

console.log('Все тесты MarkdownShield успешно пройдены!');
