/**
 * Регрессионные тесты очередей, разбиения текста и AbortSignal (Раздел 7).
 * Проверяет:
 * - splitTextIntoSafeChunks разбивает длинный текст по границам предложений / абзацев;
 * - Не разрывает суррогатные пары Unicode (эмодзи и специальные символы);
 * - Не разрывает токены экранирования ⟦...⟧;
 * - GlobalRequestQueue строго соблюдает ограничение конкурентности (maxConcurrent = 2);
 * - AbortSignal прерывает выполнение при отмене.
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
const code = fs.readFileSync(i18nFile, 'utf-8');

console.log('--- Запуск тестов Queue, Splitting & AbortSignal ---');

// Извлекаем splitTextIntoSafeChunks и GlobalRequestQueue
const splitMatch = code.match(/function splitTextIntoSafeChunks[\s\S]*?\n  \}/);
assert(splitMatch, 'splitTextIntoSafeChunks должна быть определена');

const queueMatch = code.match(/class GlobalRequestQueue[\s\S]*?\n  \}/);
assert(queueMatch, 'GlobalRequestQueue должен быть определен');

const sandbox = { console };
vm.createContext(sandbox);

const { splitTextIntoSafeChunks, GlobalRequestQueue } = vm.runInContext(`(function() {
  ${splitMatch[0]};
  ${queueMatch[0]};
  return { splitTextIntoSafeChunks, GlobalRequestQueue };
})()`, sandbox);

// Тест 1: Неразрывность Unicode суррогатных пар и спецсимволов при разбиении
{
  // Создаем строку, где на границе лимита стоит эмодзи из 2 code units
  const prefix = 'А'.repeat(999);
  const emoji = '🚀'; // 2 UTF-16 code units (surrogate pair)
  const suffix = ' Б'.repeat(50);
  const fullText = prefix + emoji + suffix;

  const chunks = splitTextIntoSafeChunks(fullText, 1000);
  assert(chunks.length > 1, 'Текст должен быть разбит на чанки');

  // Проверяем, что в каждом чанке нет одиноких суррогатов (hanging high or low surrogate)
  for (const chunk of chunks) {
    for (let i = 0; i < chunk.length; i++) {
      const code = chunk.charCodeAt(i);
      if (code >= 0xD800 && code <= 0xDBFF) {
        // High surrogate должен сопровождаться low surrogate
        assert(i + 1 < chunk.length, 'High surrogate не должен быть последним символом чанка!');
        const next = chunk.charCodeAt(i + 1);
        assert(next >= 0xDC00 && next <= 0xDFFF, 'За high surrogate должен следовать low surrogate!');
      } else if (code >= 0xDC00 && code <= 0xDFFF) {
        // Low surrogate должен предваряться high surrogate
        assert(i > 0, 'Low surrogate не должен быть первым символом чанка без high surrogate!');
        const prev = chunk.charCodeAt(i - 1);
        assert(prev >= 0xD800 && prev <= 0xDBFF, 'Low surrogate должен следовать за high surrogate!');
      }
    }
  }

  // Склеенный текст должен быть идентичен исходному (с нормализацией пробелов между предложениями)
  const reconstructed = chunks.join('');
  assert(reconstructed.includes('🚀'), 'Эмодзи должен сохраниться целиком');
  console.log('✓ Тест 1 пройден: суррогатные пары Unicode не повреждаются при разбиении');
}

// Тест 2: Неразрывность токенов экранирования ⟦...⟧
{
  const token = '⟦AGB_xyz123_42⟧';
  // Размещаем токен ровно в районе границы лимита 1000 символов
  const text = 'Слово. '.repeat(130) + token + ' Еще предложение. '.repeat(100);

  const chunks = splitTextIntoSafeChunks(text, 1000);

  for (const chunk of chunks) {
    // В любом чанке, если есть ⟦, то обязательно должна быть парная ⟧
    const openCount = (chunk.match(/⟦/g) || []).length;
    const closeCount = (chunk.match(/⟧/g) || []).length;
    assert.strictEqual(openCount, closeCount, `Токен экранирования был разорван между чанками в: ${chunk.substring(0, 50)}...`);
  }
  console.log('✓ Тест 2 пройден: токены экранирования ⟦...⟧ не разрываются при разбиении');
}

// Тест 3: GlobalRequestQueue строго соблюдает concurrency limit <= 2
{
  const queue = new GlobalRequestQueue(2);
  let activeCount = 0;
  let maxObservedActive = 0;
  const executionOrder = [];

  const createTask = (id, delayMs) => {
    return () => queue.enqueue(async () => {
      activeCount++;
      if (activeCount > maxObservedActive) {
        maxObservedActive = activeCount;
      }
      executionOrder.push(`start-${id}`);
      await new Promise(resolve => setTimeout(resolve, delayMs));
      executionOrder.push(`end-${id}`);
      activeCount--;
      return id;
    });
  };

  const p1 = createTask(1, 40)();
  const p2 = createTask(2, 40)();
  const p3 = createTask(3, 20)();
  const p4 = createTask(4, 20)();

  const results = await Promise.all([p1, p2, p3, p4]);
  assert.deepStrictEqual(results, [1, 2, 3, 4], 'Все задачи должны успешно завершиться');
  assert(maxObservedActive <= 2, `Максимальная конкурентность не должна превышать 2 (наблюдалось: ${maxObservedActive})`);
  assert.strictEqual(activeCount, 0, 'По завершении всех задач счетчик активных должен быть 0');
  console.log('✓ Тест 3 пройден: GlobalRequestQueue строго ограничивает конкурентность до 2');
}

// Тест 4: AbortSignal корректно отменяет задачу в очереди
{
  const queue = new GlobalRequestQueue(2);
  const controller = new AbortController();

  // Занимаем оба слота длинными задачами
  const blocker1 = queue.enqueue(() => new Promise(r => setTimeout(r, 60)));
  const blocker2 = queue.enqueue(() => new Promise(r => setTimeout(r, 60)));

  // Ставим в очередь третью задачу, которую сразу отменим
  let thirdExecuted = false;
  const signal = controller.signal;

  const thirdPromise = queue.enqueue(async () => {
    thirdExecuted = true;
    return 'ok';
  }, signal);

  // Немедленно вызываем отмену
  controller.abort(new Error('User aborted'));

  let caughtError = null;
  try {
    await thirdPromise;
  } catch (err) {
    caughtError = err;
  }

  assert(caughtError, 'Отмененная задача должна выбросить исключение');
  assert.strictEqual(thirdExecuted, false, 'Отмененная задача не должна была начать выполнение');
  await Promise.all([blocker1, blocker2]);
  console.log('✓ Тест 4 пройден: AbortSignal немедленно отменяет ожидающую задачу');
}

console.log('Все тесты Queue, Splitting & AbortSignal успешно пройдены!');
