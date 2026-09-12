import os
import sys
import json
import time
import urllib.request
import urllib.parse

def get_env():
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    conf = {}
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    conf[k.strip()] = v.strip()
    return conf, env_file

def save_env(updates):
    conf, env_file = get_env()
    conf.update(updates)
    with open(env_file, 'w', encoding='utf-8') as f:
        for k, v in conf.items():
            f.write(f'{k}={v}\n')

def detect_chat(token):
    print("[*] Ожидание сообщений от бота @Upgitpro_bot...")
    print("[*] Добавьте бота в группу и напишите любое сообщение в нужной теме, упомянув @Upgitpro_bot")
    offset = 0
    start_time = time.time()
    while time.time() - start_time < 180:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=5"
            req = urllib.request.Request(url)
            data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
            if data.get('ok') and data.get('result'):
                for item in data['result']:
                    offset = item['update_id'] + 1
                    msg = item.get('message') or item.get('channel_post') or item.get('my_chat_member')
                    if msg:
                        chat = msg.get('chat', {})
                        chat_id = chat.get('id')
                        chat_title = chat.get('title', 'Личный чат')
                        thread_id = msg.get('message_thread_id')
                        print(f"[+] Обнаружен чат: \"{chat_title}\" (ID: {chat_id})")
                        if thread_id:
                            print(f"[+] Обнаружена тема (Thread ID): {thread_id}")
                        else:
                            print("[*] Сообщение в основном канале (без thread_id)")
                        save_env({'TG_CHAT_ID': str(chat_id), 'TG_THREAD_ID': str(thread_id or '')})
                        print("[+] Настройки успешно сохранены в .env!")
                        return chat_id, thread_id
        except Exception as e:
            pass
        time.sleep(1)
    print("[-] Время ожидания истекло.")
    return None, None

def send_message(token, chat_id, text, thread_id=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    if thread_id:
        payload['message_thread_id'] = int(thread_id)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    return res

def send_document(token, chat_id, file_path, caption='', thread_id=None):
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    boundary = '----WebKitFormBoundary' + hex(int(time.time() * 1000))[2:]
    
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    filename = os.path.basename(file_path)
    body = bytearray()
    
    def add_field(name, value):
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode('utf-8'))
        body.extend(f'{value}\r\n'.encode('utf-8'))
        
    add_field('chat_id', str(chat_id))
    if thread_id:
        add_field('message_thread_id', str(thread_id))
    if caption:
        add_field('caption', caption)
        add_field('parse_mode', 'HTML')
        
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode('utf-8'))
    body.extend(b'Content-Type: application/octet-stream\r\n\r\n')
    body.extend(file_bytes)
    body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    
    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    return res

if __name__ == '__main__':
    conf, _ = get_env()
    token = conf.get('TG_BOT_TOKEN')
    if not token:
        print('[-] Не задан TG_BOT_TOKEN в .env')
        sys.exit(1)
        
    if len(sys.argv) > 1 and sys.argv[1] == '--detect':
        detect_chat(token)
    elif len(sys.argv) > 1 and sys.argv[1] == '--test':
        chat_id = conf.get('TG_CHAT_ID')
        thread_id = conf.get('TG_THREAD_ID')
        if not chat_id:
            print('[-] Не задан TG_CHAT_ID. Запустите с --detect')
            sys.exit(1)
        print(f'[*] Отправка тестового сообщения в {chat_id} (тема: {thread_id})...')
        msg = send_message(token, chat_id, '<b>[Тест]</b> Бот подключён к Antigravity Localizer! Готов публиковать релизы.', thread_id)
        print('[+] Сообщение отправлено:', msg.get('ok'))
