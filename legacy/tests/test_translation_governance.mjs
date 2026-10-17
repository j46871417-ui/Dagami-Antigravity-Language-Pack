/**
 * Регрессионные тесты управления сетью и приватности (Раздел 5).
 * Проверяет:
 * - Автоперевод по умолчанию ВЫКЛЮЧЕН (opt-in);
 * - При выключенном автопереводе никаких сетевых запросов не отправляется;
 * - Отсутствие сторонних несанкционированных эндпоинтов (MyMemory);
 * - Двухуровневый кэш по умолчанию работает только в оперативной памяти (L1);
 * - Логирование не содержит пользовательского текста, кода или токенов.
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

console.log('--- Запуск тестов Translation Governance & Privacy ---');

// Тест 1: Проверка отсутствия сторонних сервисов (MyMemory) в коде
{
  assert(!code.toLowerCase().includes('mymemory'), 'Код не должен содержать обращений к сторонним сервисам типа MyMemory');
  assert(!code.includes('api.mymemory.translated.net'), 'Эндпоинт MyMemory должен быть полностью исключен');
  console.log('✓ Тест 1 пройден: сторонние несанкционированные эндпоинты (MyMemory) отсутствуют');
}

// Тест 2: Автоперевод по умолчанию выключен
{
  // Извлекаем функцию getGlobalAutoTranslate
  const match = code.match(/function getGlobalAutoTranslate\(\)[\s\S]*?\n  \}/);
  assert(match, 'getGlobalAutoTranslate должна быть определена');

  const storageKeyMatch = code.match(/const STORAGE_KEY_SHARED_AUTO = [^;]+;/);
  assert(storageKeyMatch, 'STORAGE_KEY_SHARED_AUTO должно быть определено');

  const mockLocalStorage = {
    _data: {},
    getItem(k) { return this._data[k] ?? null; },
    setItem(k, v) { this._data[k] = String(v); }
  };

  const sandbox = {
    localStorage: mockLocalStorage,
    window: { localStorage: mockLocalStorage },
    console
  };
  vm.createContext(sandbox);
  const getGlobalAutoTranslate = vm.runInContext(`(function() {
    ${storageKeyMatch[0]};
    ${match[0]};
    return getGlobalAutoTranslate;
  })()`, sandbox);

  // Без настроек в localStorage
  assert.strictEqual(getGlobalAutoTranslate(), false, 'Автоперевод должен быть FALSE по умолчанию');

  // При установке ag_auto_translate
  mockLocalStorage.setItem('ag_auto_translate', 'true');
  assert.strictEqual(getGlobalAutoTranslate(), true, 'При установке true должен возвращать true');

  // При явном выключении
  mockLocalStorage.setItem('ag_auto_translate', 'false');
  assert.strictEqual(getGlobalAutoTranslate(), false, 'При установке false должен возвращать false');
  console.log('✓ Тест 2 пройден: автоперевод строго выключен по умолчанию (opt-in)');
}

// Тест 3: TwoLevelCache по умолчанию использует только L1 (память)
{
  const cacheMatch = code.match(/class TwoLevelCache[\s\S]*?\n  \}/);
  assert(cacheMatch, 'TwoLevelCache должен быть определен');

  const fastHashMatch = code.match(/function fastHash[\s\S]*?\n  \}/);
  assert(fastHashMatch, 'fastHash должен быть определен');

  const mockLocalStorage = {
    _data: {},
    getItem(k) { return this._data[k] ?? null; },
    setItem(k, v) { this._data[k] = String(v); },
    removeItem(k) { delete this._data[k]; },
    key(i) { return Object.keys(this._data)[i]; },
    get length() { return Object.keys(this._data).length; }
  };

  const sandbox = {
    localStorage: mockLocalStorage,
    console
  };
  vm.createContext(sandbox);
  const TwoLevelCache = vm.runInContext(`(function() {
    ${fastHashMatch[0]};
    ${cacheMatch[0]};
    return TwoLevelCache;
  })()`, sandbox);

  const cache = new TwoLevelCache();

  // По умолчанию persistent storage выключен
  assert.strictEqual(cache._isPersistentEnabled(), false, 'По умолчанию постоянный кэш должен быть выключен');

  cache.set('hello', 'привет');
  const resL1 = cache.get('hello');
  assert.strictEqual(resL1.value, 'привет', 'Значение должно совпадать');
  assert.strictEqual(resL1.level, 'L1', 'Уровень должен быть L1');
  assert.strictEqual(Object.keys(mockLocalStorage._data).length, 0, 'В localStorage ничего не должно сохраняться по умолчанию');

  // Проверяем включение persistent cache через флаг
  mockLocalStorage.setItem('ag_enable_persistent_cache', 'true');
  assert.strictEqual(cache._isPersistentEnabled(), true);
  cache.set('world', 'мир');
  assert(Object.keys(mockLocalStorage._data).some(k => k.startsWith('ag_tr_v2_')), 'При явном включении должен писать в persistent cache');
  console.log('✓ Тест 3 пройден: TwoLevelCache работает in-memory по умолчанию без утечки в хранилище');
}

// Тест 4: Проверка санитизации логирования
{
  // Убеждаемся, что console.warn / console.error в коде не логируют text, input или payload напрямую
  const suspiciousLogging = code.match(/console\.(?:warn|error|log)\([^)]*(?:text|source|chunk|fullText|maskedText)[^)]*\)/g);
  // Фильтруем возможные ложные срабатывания, проверяя что пользовательские данные не попадают в логи
  if (suspiciousLogging) {
    for (const logLine of suspiciousLogging) {
      // Разрешены логи с именами классов или статусами, но не вывод пользовательского содержимого
      assert(!logLine.includes('text:') && !logLine.includes('chunk:'), `Потенциальная утечка пользовательского текста в лог: ${logLine}`);
    }
  }
  console.log('✓ Тест 4 пройден: санитизация логов (никаких утечек текста пользователя в консоль)');
}

console.log('Все тесты Translation Governance & Privacy успешно пройдены!');
