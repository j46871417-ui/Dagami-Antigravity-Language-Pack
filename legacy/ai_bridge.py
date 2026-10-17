import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# Prototype AI Bridge:
# Listens on 127.0.0.1:51122
# Routes incoming Gemini API requests:
#   POST /v1beta/models/{model}:streamGenerateContent
#   POST /v1beta/models/{model}:generateContent
# Translates to configured OpenAI-compatible endpoint (Ollama, OpenRouter, DeepSeek, etc.)

CONFIG = {
    "providers": {
        "ollama": {
            "api_base": "http://127.0.0.1:11434/v1",
            "api_key": "ollama"
        },
        "deepseek": {
            "api_base": "https://api.deepseek.com/v1",
            "api_key": ""
        },
        "openrouter": {
            "api_base": "https://openrouter.ai/api/v1",
            "api_key": ""
        }
    },
    "model_mapping": {
        # e.g. "my-llama": {"provider": "ollama", "target_model": "llama3:latest"}
    }
}

def gemini_contents_to_openai_messages(contents):
    messages = []
    for item in contents:
        role = item.get("role", "user")
        if role == "model":
            role = "assistant"
        parts = item.get("parts", [])
        text_parts = []
        for p in parts:
            if "text" in p:
                text_parts.append(p["text"])
        messages.append({
            "role": role,
            "content": "\n".join(text_parts)
        })
    return messages

class AIBridgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path = self.path
        is_stream = "streamGenerateContent" in path
        
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        req_json = json.loads(post_data.decode("utf-8")) if post_data else {}
        
        model_part = path.split("/v1beta/models/")[-1].split(":")[0]
        
        print(f"[AI Bridge] Request for model: {model_part}, stream={is_stream}")
        
        target_model = model_part
        provider_name = "ollama"
        if model_part in CONFIG["model_mapping"]:
            m_info = CONFIG["model_mapping"][model_part]
            provider_name = m_info.get("provider", "ollama")
            target_model = m_info.get("target_model", model_part)
            
        provider_cfg = CONFIG["providers"].get(provider_name, CONFIG["providers"]["ollama"])
        api_base = provider_cfg["api_base"].rstrip("/")
        api_key = provider_cfg.get("api_key", "")
        
        messages = gemini_contents_to_openai_messages(req_json.get("contents", []))
        openai_req = {
            "model": target_model,
            "messages": messages,
            "stream": is_stream
        }
        
        openai_url = f"{api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        req = urllib.request.Request(
            openai_url,
            data=json.dumps(openai_req).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            resp = urllib.request.urlopen(req)
            if is_stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if not line_str.startswith("data:"):
                        continue
                    payload = line_str[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            gemini_chunk = {
                                "candidates": [{
                                    "content": {
                                        "parts": [{"text": content}],
                                        "role": "model"
                                    }
                                }]
                            }
                            out_sse = f"data: {json.dumps(gemini_chunk)}\n\n"
                            self.wfile.write(out_sse.encode("utf-8"))
                            self.wfile.flush()
                    except Exception:
                        pass
            else:
                resp_data = resp.read().decode("utf-8")
                openai_resp = json.loads(resp_data)
                content = openai_resp["choices"][0]["message"]["content"]
                gemini_resp = {
                    "candidates": [{
                        "content": {
                            "parts": [{"text": content}],
                            "role": "model"
                        }
                    }]
                }
                out_bytes = json.dumps(gemini_resp).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out_bytes)))
                self.end_headers()
                self.wfile.write(out_bytes)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            print(f"[AI Bridge Error]: {err_body}")
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(err_body.encode("utf-8"))
        except Exception as e:
            print(f"[AI Bridge Exception]: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

def run_server(port=51122):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, AIBridgeHandler)
    print(f"[AI Bridge] Listening on http://127.0.0.1:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 51122
    run_server(port)
