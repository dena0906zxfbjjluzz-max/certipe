"""Servidor HTTP (stdlib) + UI del emisor/validador."""

from __future__ import annotations

import html
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from app import certificates, crypto

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE / "static"
HOST = "127.0.0.1"
PORT = 8000


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _layout(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <div class="bg"></div>
  <header class="top">
    <a class="brand" href="/">CertiPE</a>
    <nav>
      <a href="/emitir">Emitir</a>
      <a href="/validar">Validar</a>
    </nav>
  </header>
  <main class="wrap">{body}</main>
  <footer class="foot">MVP · Ed25519 (OpenSSL) · sin blockchain · demo institucional</footer>
</body>
</html>"""


def _result_panel(result: dict) -> str:
    ok = result.get("ok")
    klass = "ok" if ok else "bad"
    title = "Auténtico" if ok else "No válido"
    cert = result.get("certificate")
    extra = ""
    if cert:
        extra = f"""
        <dl class="meta">
          <div><dt>Titular</dt><dd>{_esc(cert.get('holder_name'))}</dd></div>
          <div><dt>Documento</dt><dd>{_esc(cert.get('holder_doc'))}</dd></div>
          <div><dt>Curso</dt><dd>{_esc(cert.get('course_title'))}</dd></div>
          <div><dt>Institución</dt><dd>{_esc(cert.get('institution_name'))}</dd></div>
          <div><dt>Emitido</dt><dd>{_esc(cert.get('issued_at'))}</dd></div>
          <div><dt>Estado</dt><dd class="tag {_esc(cert.get('status'))}">{_esc(cert.get('status'))}</dd></div>
          <div><dt>Firma OK</dt><dd>{_esc(result.get('signature_valid'))}</dd></div>
          <div><dt>Hash OK</dt><dd>{_esc(result.get('hash_valid'))}</dd></div>
        </dl>
        <p><a class="btn ghost" href="/c/{_esc(cert.get('id'))}">Ver certificado</a></p>
        """
    return f"""
    <section class="panel result {klass}">
      <h2>{title}</h2>
      <p>{_esc(result.get('message'))}</p>
      {extra}
    </section>
    """


def page_home() -> str:
    crypto.ensure_keys()
    certs = certificates.list_all()[:20]
    items = ""
    for c in certs:
        items += f"""
        <li>
          <a href="/c/{_esc(c['id'])}">{_esc(c['id'])}</a>
          <span>{_esc(c['holder_name'])} · {_esc(c['course_title'])}</span>
          <span class="tag {_esc(c['status'])}">{_esc(c['status'])}</span>
        </li>"""
    recent = f"""
    <section class="panel">
      <h2>Últimos emitidos</h2>
      <ul class="list">{items or '<li><span>Aún no hay certificados.</span></li>'}</ul>
    </section>""" if True else ""
    return _layout(
        "CertiPE · Emisor",
        f"""
        <section class="hero">
          <p class="eyebrow">{_esc(certificates.INSTITUTION_NAME)}</p>
          <h1>Certificados firmados con Ed25519</h1>
          <p class="lead">
            Emite un certificado, fírmalo con la clave de la institución y compártelo.
            Cualquiera puede verificar si es auténtico o si lo alteraron.
          </p>
          <div class="actions">
            <a class="btn primary" href="/emitir">Emitir certificado</a>
            <a class="btn ghost" href="/validar">Validar código</a>
          </div>
        </section>
        <section class="panel">
          <h2>Clave pública de la institución</h2>
          <p class="muted">Huella: <code>{_esc(crypto.public_key_fingerprint())}</code>. La privada nunca sale del servidor.</p>
          <code class="key">{_esc(crypto.public_key_b64())}</code>
        </section>
        {recent}
        """,
    )


def page_emitir() -> str:
    return _layout(
        "Emitir · CertiPE",
        f"""
        <section class="panel narrow">
          <h1>Emitir certificado</h1>
          <p class="muted">{_esc(certificates.INSTITUTION_NAME)} firmará con Ed25519.</p>
          <form method="post" action="/emitir" class="form">
            <label>Nombre del titulado
              <input name="holder_name" required maxlength="200" placeholder="Ana López" />
            </label>
            <label>Documento (DNI / CE)
              <input name="holder_doc" required maxlength="32" placeholder="12345678" />
            </label>
            <label>Curso / programa
              <input name="course_title" required maxlength="300" placeholder="Introducción a Python" />
            </label>
            <label>Horas (opcional)
              <input name="course_hours" type="number" min="1" max="10000" placeholder="40" />
            </label>
            <label>Firmado por (opcional)
              <input name="issued_by" maxlength="200" placeholder="Director académico" />
            </label>
            <label>Notas (opcional)
              <textarea name="notes" rows="3" maxlength="500"></textarea>
            </label>
            <button class="btn primary" type="submit">Firmar y emitir</button>
          </form>
        </section>
        """,
    )


def page_validar(codigo: str = "", result: dict | None = None) -> str:
    block = _result_panel(result) if result is not None else ""
    return _layout(
        "Validar · CertiPE",
        f"""
        <section class="panel narrow">
          <h1>Validar certificado</h1>
          <p class="muted">Ingresa el código (ej. CERT-XXXX-XXXX-XXXX).</p>
          <form method="post" action="/validar" class="form">
            <label>Código
              <input name="codigo" value="{_esc(codigo)}" required placeholder="CERT-...." />
            </label>
            <button class="btn primary" type="submit">Verificar firma</button>
          </form>
        </section>
        {block}
        """,
    )


def page_cert(base_url: str, cert_id: str) -> str | None:
    result = certificates.validate(cert_id)
    if result["reason"] == "not_found":
        return None
    cert = result["certificate"]
    verify_url = f"{base_url.rstrip('/')}/v/{cert['id']}"
    banner = (
        '<p class="banner ok">Firma válida · no alterado</p>'
        if result["ok"]
        else f'<p class="banner bad">{_esc(result["message"])}</p>'
    )
    hours = (
        f'<p class="muted">{_esc(cert.get("course_hours"))} horas académicas</p>'
        if cert.get("course_hours")
        else ""
    )
    return _layout(
        f"{cert['id']} · CertiPE",
        f"""
        <section class="cert-sheet">
          <div class="cert-head">
            <div>
              <p class="eyebrow">{_esc(cert.get('institution_name'))}</p>
              <h1>Certificado de participación</h1>
              <p class="lead">Se certifica que</p>
              <p class="holder">{_esc(cert.get('holder_name'))}</p>
              <p class="muted">Doc. {_esc(cert.get('holder_doc'))}</p>
              <p class="lead mid">completó el programa</p>
              <p class="course">{_esc(cert.get('course_title'))}</p>
              {hours}
            </div>
            <div class="qr-box">
              <p class="tiny"><strong>Enlace de validación</strong></p>
              <p class="tiny break"><a href="{_esc(verify_url)}">{_esc(verify_url)}</a></p>
              <p class="tiny">Abre o comparte este link (QR en fase 2).</p>
            </div>
          </div>
          <dl class="meta">
            <div><dt>Código</dt><dd><code>{_esc(cert.get('id'))}</code></dd></div>
            <div><dt>Emitido</dt><dd>{_esc(cert.get('issued_at'))}</dd></div>
            <div><dt>Estado</dt><dd class="tag {_esc(cert.get('status'))}">{_esc(cert.get('status'))}</dd></div>
            <div><dt>Algoritmo</dt><dd>{_esc(cert.get('alg'))}</dd></div>
            <div><dt>Hash SHA-256</dt><dd class="break"><code>{_esc(cert.get('payload_hash'))}</code></dd></div>
            <div><dt>Firma</dt><dd class="break"><code>{_esc(cert.get('signature'))}</code></dd></div>
          </dl>
          {banner}
        </section>
        """,
    )


def page_public_verify(cert_id: str) -> str:
    result = certificates.validate(cert_id)
    return _layout(
        f"Resultado {cert_id} · CertiPE",
        f"""
        <section class="panel">
          <h1>Verificación pública</h1>
          <p class="muted">Código <code>{_esc(cert_id)}</code></p>
        </section>
        {_result_panel(result)}
        """,
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "CertiPE/0.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[certipe] {self.address_string()} {fmt % args}")

    def _base(self) -> str:
        host = self.headers.get("Host", f"{HOST}:{PORT}")
        return f"http://{host}"

    def _send(self, code: int, body: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _html(self, code: int, page: str) -> None:
        self._send(code, page.encode("utf-8"), "text/html; charset=utf-8")

    def _json(self, code: int, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _redirect(self, location: str) -> None:
        self._send(303, b"", "text/plain", {"Location": location})

    def _read_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b""
        parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
        return {k: (v[0] if v else "") for k, v in parsed.items()}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        qs = parse_qs(parsed.query)

        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            if ".." in rel or rel.startswith("/"):
                self._send(400, b"bad path", "text/plain")
                return
            file_path = STATIC_DIR / rel
            if not file_path.is_file():
                self._send(404, b"not found", "text/plain")
                return
            data = file_path.read_bytes()
            ctype = "text/css" if file_path.suffix == ".css" else "application/octet-stream"
            self._send(200, data, ctype)
            return

        if path == "/":
            self._html(200, page_home())
            return
        if path == "/emitir":
            self._html(200, page_emitir())
            return
        if path == "/validar":
            codigo = (qs.get("codigo") or [""])[0]
            result = certificates.validate(codigo.strip().upper()) if codigo else None
            self._html(200, page_validar(codigo, result))
            return

        m = re.fullmatch(r"/c/(CERT-[A-Za-z0-9-]+)", path)
        if m:
            page = page_cert(self._base(), m.group(1).upper())
            if page is None:
                self._html(404, _layout("404", "<section class='panel'><h1>No encontrado</h1></section>"))
            else:
                self._html(200, page)
            return

        m = re.fullmatch(r"/v/(CERT-[A-Za-z0-9-]+)", path)
        if m:
            self._html(200, page_public_verify(m.group(1).upper()))
            return

        if path == "/api/public-key":
            self._json(200, {"alg": "Ed25519", "public_key": crypto.public_key_b64(), "fingerprint": crypto.public_key_fingerprint()})
            return
        if path == "/api/certs":
            self._json(200, certificates.list_all())
            return
        m = re.fullmatch(r"/api/validate/(CERT-[A-Za-z0-9-]+)", path)
        if m:
            self._json(200, certificates.validate(m.group(1).upper()))
            return

        self._html(404, _layout("404", "<section class='panel'><h1>Ruta no encontrada</h1></section>"))

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        form = self._read_form()

        if path == "/emitir":
            hours_raw = (form.get("course_hours") or "").strip()
            hours = int(hours_raw) if hours_raw.isdigit() else None
            rec = certificates.issue(
                holder_name=form.get("holder_name", ""),
                holder_doc=form.get("holder_doc", ""),
                course_title=form.get("course_title", ""),
                course_hours=hours,
                issued_by=form.get("issued_by") or None,
                notes=form.get("notes") or None,
            )
            self._redirect(f"/c/{rec['id']}")
            return

        if path == "/validar":
            codigo = (form.get("codigo") or "").strip()
            self._redirect(f"/validar?codigo={codigo}")
            return

        if path.startswith("/api/issue"):
            try:
                length = int(self.headers.get("Content-Length", "0") or 0)
                data = json.loads(self.rfile.read(length) or b"{}")
                rec = certificates.issue(
                    holder_name=data["holder_name"],
                    holder_doc=data["holder_doc"],
                    course_title=data["course_title"],
                    course_hours=data.get("course_hours"),
                    issued_by=data.get("issued_by"),
                    notes=data.get("notes"),
                )
                self._json(200, rec)
            except Exception as exc:  # noqa: BLE001
                self._json(400, {"error": str(exc)})
            return

        m = re.fullmatch(r"/api/revoke/(CERT-[A-Za-z0-9-]+)", path)
        if m:
            rec = certificates.revoke(m.group(1).upper())
            if not rec:
                self._json(404, {"error": "No encontrado"})
            else:
                self._json(200, rec)
            return

        self._json(404, {"error": "Ruta no encontrada"})


def main() -> None:
    crypto.ensure_keys()
    STATIC_DIR.mkdir(exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"CertiPE listo → http://{HOST}:{PORT}")
    print("  Emite:   /emitir")
    print("  Valida:  /validar")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")
        httpd.server_close()


if __name__ == "__main__":
    main()
