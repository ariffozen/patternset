import base64
import json
import logging
import os
import subprocess

from flask import Flask, request, render_template_string

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)

DEFAULT_DEVICE = os.getenv("PATSET_DEVICE", "")
PATSET_PATH = "/nitro/v1/config/policypatset_pattern_binding/"
DEFAULT_PATSET_NAME = os.getenv("PATSET_NAME", "")
DEFAULT_AUTH_HEADER = os.getenv("PATSET_AUTH_HEADER", "")
DEFAULT_USERNAME = os.getenv("PATSET_USERNAME", "")
DEFAULT_PASSWORD = os.getenv("PATSET_PASSWORD", "")
DEFAULT_PATTERNS_TEXT = os.getenv("PATSET_DEFAULT_PATTERNS", "")


PAGE_TEMPLATE = """
<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Patset Yükleyici</title>
  <style>
    :root {
      --primary: #FF671D;
      --primary-dark: #e55b16;
      --primary-light: #ff8347;
      --bg: #0f1115;
      --bg-accent: #141821;
      --card: #1b202b;
      --text: #f7f8fa;
      --muted: #9ba6b2;
      --border: rgba(255,255,255,0.08);
      --success: #3bd179;
      --error: #ff6b6b;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background:
        radial-gradient(circle at 8% 12%, rgba(255, 103, 29, 0.36), transparent 55%),
        radial-gradient(circle at 92% 18%, rgba(255, 103, 29, 0.16), transparent 45%),
        linear-gradient(180deg, var(--bg), var(--bg-accent));
      color: var(--text);
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 48px 16px;
    }

    .shell {
      width: min(1080px, 100%);
      display: flex;
      flex-direction: column;
      gap: 32px;
    }

    header {
      display: flex;
      align-items: center;
      gap: 18px;
    }

    .badge {
      width: 56px;
      height: 56px;
      border-radius: 18px;
      background: linear-gradient(135deg, var(--primary), var(--primary-light));
      display: flex;
      align-items: center;
      justify-content: center;
      color: #111;
      font-weight: 700;
      font-size: 1.35rem;
      box-shadow: 0 22px 55px -35px var(--primary);
    }

    header h1 {
      margin: 0;
      font-size: 2.2rem;
      letter-spacing: 0.01em;
    }

    header p {
      margin: 4px 0 0 0;
      color: var(--muted);
      max-width: 560px;
    }

    .card {
      background: var(--card);
      border-radius: 24px;
      padding: 34px;
      border: 1px solid var(--border);
      box-shadow: 0 28px 60px -45px rgba(0, 0, 0, 0.65);
    }

    .form-grid {
      display: grid;
      gap: 20px;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    label {
      font-size: 0.92rem;
      font-weight: 600;
      color: var(--text);
    }

    input, textarea {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      color: var(--text);
      padding: 14px 16px;
      font-size: 0.96rem;
      transition: border 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }

    input::placeholder, textarea::placeholder {
      color: rgba(255, 255, 255, 0.35);
    }

    input:focus, textarea:focus {
      outline: none;
      border-color: var(--primary-light);
      box-shadow: 0 18px 45px -35px var(--primary);
      transform: translateY(-1px);
    }

    textarea {
      min-height: 220px;
      resize: vertical;
      grid-column: 1 / -1;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      line-height: 1.48;
    }

    .hint {
      grid-column: 1 / -1;
      font-size: 0.84rem;
      color: var(--muted);
      margin-top: -6px;
    }

    .actions {
      grid-column: 1 / -1;
      display: flex;
      justify-content: flex-end;
    }

    button {
      background: linear-gradient(135deg, var(--primary), var(--primary-light));
      border: none;
      border-radius: 14px;
      padding: 15px 30px;
      font-weight: 600;
      letter-spacing: 0.02em;
      color: #111;
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 22px 45px -28px var(--primary);
    }

    button:active {
      transform: translateY(0);
    }

    .error-banner {
      margin-top: 20px;
      background: rgba(255, 107, 107, 0.12);
      border: 1px solid rgba(255, 107, 107, 0.3);
      color: var(--error);
      padding: 18px 22px;
      border-radius: 18px;
      font-weight: 500;
    }

    .results-card {
      margin-top: 28px;
      border-radius: 22px;
      overflow: hidden;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.02);
    }

    .results-card h2 {
      margin: 0;
      padding: 24px 30px;
      background: rgba(255, 103, 29, 0.12);
      color: var(--primary-light);
      font-size: 1.2rem;
      letter-spacing: 0.02em;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    thead {
      background: rgba(255, 255, 255, 0.03);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: rgba(255, 255, 255, 0.6);
    }

    th, td {
      text-align: left;
      padding: 16px 24px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      vertical-align: top;
    }

    tbody tr:last-child td {
      border-bottom: none;
    }

    .status-ok {
      color: var(--success);
      font-weight: 600;
    }

    .status-fail {
      color: var(--error);
      font-weight: 600;
    }

    pre {
      margin: 0;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 0.85rem;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--muted);
    }

    .summary-bar {
      padding: 18px 24px;
      background: rgba(255, 255, 255, 0.03);
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      font-weight: 600;
      color: rgba(255, 255, 255, 0.7);
      text-align: right;
    }

    @media (max-width: 760px) {
      body { padding: 32px 14px; }
      header { flex-direction: column; align-items: flex-start; }
      header h1 { font-size: 1.8rem; }
      .card { padding: 24px; }
      th, td { padding: 14px 16px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="badge">PT</div>
      <div>
        <h1>Patset Yükleyici</h1>
        <p>NetScaler patset yapılandırmalarını tek ekrandan yönetin. Cihazınızı, patset adınızı ve göndermek istediğiniz desenleri girin; diğer her şey saniyeler içinde tamamlanır.</p>
      </div>
    </header>

    <section class="card">
      <form method="post" class="form-grid">
        <div class="form-group">
          <label for="device">Cihaz IP / Host</label>
          <input id="device" name="device" type="text" value="{{ device_value|e }}" placeholder="örn. 198.51.100.10" required>
        </div>
        <div class="form-group">
          <label for="patset">Patset Adı</label>
          <input id="patset" name="patset" type="text" value="{{ patset_value|e }}" placeholder="örn. example_patset_name" required>
        </div>
        <div class="form-group">
          <label for="username">Kullanıcı Adı</label>
          <input id="username" name="username" type="text" value="{{ username_value|e }}" placeholder="örn. nsadmin">
        </div>
        <div class="form-group">
          <label for="password">Parola</label>
          <input id="password" name="password" type="password" placeholder="Parola girin">
        </div>
        <div class="form-group">
          <label for="auth">Authorization Header</label>
          <input id="auth" name="auth" type="password" value="{{ auth_value|e }}" placeholder="Basic ...">
        </div>
        <p class="hint">Authorization header alanını boş bırakırsanız kullanıcı adı ve parola bilgisiyle otomatik oluşturulur.</p>
        <div class="form-group" style="grid-column: 1 / -1;">
          <label for="patterns">Pattern Listesi</label>
          <textarea id="patterns" name="patterns" placeholder="Her satıra bir domain veya pattern yazın">{{ textarea_content|e }}</textarea>
        </div>
        <div class="actions">
          <button type="submit">Patset'i Güncelle</button>
        </div>
      </form>

      {% if error %}
        <div class="error-banner">{{ error }}</div>
      {% endif %}

      {% if results %}
        <div class="results-card">
          <h2>İşlem Özeti</h2>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Pattern</th>
                <th>HTTP Kod</th>
                <th>Durum</th>
                <th>Yanıt</th>
                <th>stderr</th>
              </tr>
            </thead>
            <tbody>
              {% for item in results %}
                <tr>
                  <td>{{ loop.index }} / {{ results|length }}</td>
                  <td>{{ item.pattern }}</td>
                  <td>{{ item.http_status }}</td>
                  <td>{% if item.success %}<span class="status-ok">Başarılı</span>{% else %}<span class="status-fail">Hatalı</span>{% endif %}</td>
                  <td><pre>{{ item.stdout }}</pre></td>
                  <td><pre>{{ item.stderr }}</pre></td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
          <div class="summary-bar">
            Başarılı: {{ success_count }} • Başarısız: {{ results|length - success_count }}
          </div>
        </div>
      {% endif %}
    </section>
  </div>
</body>
</html>
"""

def build_basic_auth(username: str, password: str) -> str:
    token = f"{username}:{password}"
    encoded = base64.b64encode(token.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}"


def build_payload(pattern: str, patset_name: str) -> str:
    payload = {
        "params": {"warning": "NO"},
        "policypatset_pattern_binding": {
            "name": patset_name,
            "String": [pattern],
        },
    }
    return json.dumps(payload)


def build_endpoint(device: str) -> str:
    device = device.strip()
    if not device:
        raise ValueError("Cihaz adresi boş olamaz")
    if device.startswith("http://") or device.startswith("https://"):
        base = device.rstrip("/")
    else:
        base = f"http://{device.strip('/')}"
    return f"{base}{PATSET_PATH}"


def prepare_submission(form) -> dict:
    device_value = form.get("device", DEFAULT_DEVICE).strip()
    patset_value = form.get("patset", DEFAULT_PATSET_NAME).strip()
    username_value = form.get("username", DEFAULT_USERNAME).strip()
    password_value = form.get("password", "")
    auth_value = form.get("auth", DEFAULT_AUTH_HEADER).strip()

    effective_password = password_value or DEFAULT_PASSWORD
    if not auth_value and username_value and effective_password:
        auth_value = build_basic_auth(username_value, effective_password)

    raw_patterns = form.get("patterns", "")
    patterns = [line.strip() for line in raw_patterns.splitlines() if line.strip()]

    error = None
    if not device_value:
        error = "Cihaz IP/Host boş olamaz."
    elif not patset_value:
        error = "Patset adı boş olamaz."
    elif not auth_value:
        error = "Authorization header girilmeli veya kullanıcı adı/parola belirtilmeli."
    elif not patterns:
        error = "En az bir pattern girmelisiniz."

    return {
        "device": device_value,
        "patset": patset_value,
        "username": username_value,
        "auth": auth_value,
        "patterns": patterns,
        "error": error,
    }


def send_pattern_with_curl(pattern: str, endpoint: str, patset_name: str, auth_header: str) -> dict:
    data = build_payload(pattern, patset_name)
    cmd = [
        "curl",
        "--silent",
        "--show-error",
        "--location",
        "--request",
        "PUT",
        endpoint,
        "--header",
        "Content-Type: application/json",
        "--header",
        f"Authorization: {auth_header}",
        "--data",
        data,
        "--write-out",
        "HTTPSTATUS:%{http_code}",
    ]
    logging.info("Gönderim başlıyor | pattern='%s' endpoint='%s' patset='%s'", pattern, endpoint, patset_name)
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        stdout = completed.stdout or ""
        http_status = ""
        body = stdout
        if "HTTPSTATUS:" in stdout:
            body, _, status_part = stdout.rpartition("HTTPSTATUS:")
            http_status = status_part.strip()
        if http_status == "200":
            logging.info(
                "Gönderim başarılı | pattern='%s' status=%s", pattern, http_status or "-"
            )
        else:
            logging.warning(
                "Gönderim hatalı | pattern='%s' status=%s stderr='%s'",
                pattern,
                http_status or "-",
                (completed.stderr or "").strip(),
            )
        return {
            "pattern": pattern,
            "http_status": http_status or "",
            "success": http_status == "200",
            "stdout": body.strip(),
            "stderr": (completed.stderr or "").strip(),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        logging.error(
            "Gönderim sırasında istisna oluştu | pattern='%s' error='%s'",
            pattern,
            exc,
        )
        return {
            "pattern": pattern,
            "http_status": "",
            "success": False,
            "stdout": "",
            "stderr": str(exc),
        }


@app.route("/", methods=["GET", "POST"])
def index():
    device_value = DEFAULT_DEVICE
    patset_value = DEFAULT_PATSET_NAME
    username_value = DEFAULT_USERNAME
    auth_value = DEFAULT_AUTH_HEADER
    default_text = DEFAULT_PATTERNS_TEXT
    results = None
    success_count = 0
    error = None

    if not auth_value and username_value and DEFAULT_PASSWORD:
        auth_value = build_basic_auth(username_value, DEFAULT_PASSWORD)

    if request.method == "POST":
        submission = prepare_submission(request.form)
        device_value = submission["device"]
        patset_value = submission["patset"]
        username_value = submission["username"]
        auth_value = submission["auth"]
        default_text = request.form.get("patterns", "")

        if submission["error"]:
            error = submission["error"]
            logging.warning("İstek hata ile sonuçlandı | neden='%s'", error)
        else:
            try:
                endpoint = build_endpoint(device_value)
            except ValueError as exc:
                error = str(exc)
                logging.error("Uç nokta oluşturulamadı | error='%s'", exc)
            else:
                patterns = submission["patterns"]
                logging.info(
                    "Yeni istek alındı | device='%s' patset='%s' pattern_sayısı=%d",
                    device_value,
                    patset_value,
                    len(patterns),
                )
                results = [
                    send_pattern_with_curl(pattern, endpoint, patset_value, auth_value)
                    for pattern in patterns
                ]
                success_count = sum(1 for item in results if item["success"])
                logging.info(
                    "İşlem tamamlandı | başarılı=%d başarısız=%d",
                    success_count,
                    len(results) - success_count,
                )

    return render_template_string(
        PAGE_TEMPLATE,
        textarea_content=default_text,
        device_value=device_value,
        patset_value=patset_value,
        username_value=username_value,
        auth_value=auth_value,
        results=results,
        success_count=success_count,
        error=error,
    )


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "8082"))
    app.run(host="0.0.0.0", port=port, debug=True)
