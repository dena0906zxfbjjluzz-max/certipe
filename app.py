"""
CertiPE en Streamlit — misma cara que la web local (colores y layout).
"""

from __future__ import annotations

import os
from urllib.parse import quote

import streamlit as st

from app import certificates, crypto
from app import pdf_cert

APP_VERSION = "1.2 · look web local"

st.set_page_config(
    page_title="CertiPE · Certificados",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def _secret_get(*paths: str) -> str | None:
    try:
        cur = st.secrets
        for p in paths:
            cur = cur[p]
        val = str(cur).strip()
        return val or None
    except Exception:
        return None


def bootstrap_secrets() -> None:
    seed = (
        _secret_get("LLAVE_PRIVADA")
        or _secret_get("credenciales", "LLAVE_PRIVADA")
        or os.environ.get("LLAVE_PRIVADA")
    )
    if seed:
        try:
            crypto.set_seed_hex(seed)
        except Exception as e:  # noqa: BLE001
            st.session_state["seed_error"] = str(e)

    nombre = (
        _secret_get("nombre_institucion")
        or _secret_get("credenciales", "nombre_institucion")
        or _secret_get("NOMBRE_INSTITUCION")
    )
    if nombre:
        os.environ["INSTITUTION_NAME"] = nombre

    inst_id = _secret_get("institution_id") or _secret_get("credenciales", "institution_id")
    if inst_id:
        os.environ["INSTITUTION_ID"] = inst_id


def cargar_credenciales() -> tuple[str | None, str | None, str | None]:
    try:
        creds = st.secrets["credenciales"]
        usuario = str(creds["usuario"]).strip()
        clave = str(creds["clave"]).strip()
        if not usuario or not clave:
            return None, None, "Faltan usuario/clave en secrets['credenciales']."
        return usuario, clave, None
    except Exception:
        return None, None, None


def app_base_url() -> str:
    explicit = (
        _secret_get("PUBLIC_BASE_URL")
        or _secret_get("credenciales", "PUBLIC_BASE_URL")
        or os.environ.get("PUBLIC_BASE_URL")
    )
    if explicit:
        return explicit.rstrip("/")
    try:
        headers = st.context.headers  # type: ignore[attr-defined]
        host = headers.get("Host") or headers.get("host")
        proto = headers.get("X-Forwarded-Proto") or headers.get("x-forwarded-proto") or "https"
        if host:
            return f"{proto}://{host}".rstrip("/")
    except Exception:
        pass
    return ""


def verify_url(cert_id: str) -> str:
    base = app_base_url()
    if base:
        return f"{base}/?codigo={quote(cert_id)}"
    return f"?codigo={quote(cert_id)}"


def inject_web_look() -> None:
    """Estilos calcados de static/styles.css (web local)."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700&family=IBM+Plex+Mono:wght@400;500&display=swap');

        :root {
          --ink: #14211c;
          --muted: #5b6b63;
          --ok: #1f6b45;
          --ok-bg: #e5f5eb;
          --accent: #0d6e56;
          --accent-2: #c46a1c;
          --line: #c9d5cc;
        }

        html, body, [class*="css"] {
          font-family: "DM Sans", system-ui, sans-serif !important;
          color: var(--ink);
        }

        /* Fondo como la web local */
        [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(900px 500px at 10% -10%, rgba(196, 106, 28, 0.18), transparent 55%),
            radial-gradient(800px 480px at 90% 0%, rgba(13, 110, 86, 0.18), transparent 50%),
            linear-gradient(180deg, #eef4ef 0%, #f7f5f0 45%, #e7efe9 100%) !important;
        }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stToolbar"] { right: 1rem; }

        .block-container {
          padding-top: 1rem !important;
          padding-bottom: 2.5rem !important;
          max-width: 920px !important;
        }

        /* Ocultar chrome de Streamlit sobrante */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        .top-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.8rem;
        }
        .brand {
          font-weight: 700;
          letter-spacing: -0.03em;
          font-size: 1.25rem;
          color: var(--ink);
        }
        .nav-links { color: var(--muted); font-weight: 600; font-size: 0.95rem; }

        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.12em;
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--accent-2);
          margin: 0 0 0.4rem 0;
        }
        .hero-title {
          font-size: clamp(1.8rem, 4vw, 2.55rem);
          letter-spacing: -0.04em;
          line-height: 1.15;
          font-weight: 700;
          color: var(--ink);
          margin: 0.2rem 0 0.75rem 0;
        }
        .lead {
          color: var(--muted);
          font-size: 1.05rem;
          max-width: 38rem;
          margin: 0 0 1.1rem 0;
          line-height: 1.45;
        }

        .panel {
          background: rgba(255, 255, 255, 0.88);
          border: 1px solid rgba(201, 213, 204, 0.9);
          border-radius: 18px;
          padding: 1.25rem 1.4rem;
          box-shadow: 0 18px 50px rgba(20, 33, 28, 0.08);
          backdrop-filter: blur(8px);
          margin: 0 0 1rem 0;
        }
        .panel h2 {
          margin: 0 0 0.45rem 0;
          font-size: 1.2rem;
          color: var(--ink);
        }
        .panel .muted { color: var(--muted); font-size: 0.95rem; margin: 0 0 0.7rem 0; }

        .key-box {
          display: block;
          word-break: break-all;
          background: #e9efeb;
          padding: 0.8rem 1rem;
          border-radius: 10px;
          font-family: "IBM Plex Mono", ui-monospace, monospace;
          font-size: 0.8rem;
          color: var(--ink);
          margin-top: 0.5rem;
        }

        .list-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 0;
          border-bottom: 1px solid var(--line);
          font-size: 0.95rem;
        }
        .list-row:last-child { border-bottom: none; }
        .list-id {
          font-family: "IBM Plex Mono", monospace;
          font-weight: 600;
          color: var(--accent);
          font-size: 0.9rem;
        }
        .list-meta { color: var(--muted); flex: 1; }
        .tag {
          font-size: 0.72rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          padding: 0.2rem 0.5rem;
          border-radius: 6px;
          background: var(--ok-bg);
          color: var(--ok);
          white-space: nowrap;
        }
        .tag.revoked { background: #f8e8e8; color: #8b2e2e; }

        .foot {
          text-align: center;
          color: var(--muted);
          font-size: 0.85rem;
          margin-top: 1.5rem;
        }

        /* Botones Streamlit → acento web */
        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="baseButton-primary"] {
          background-color: #0d6e56 !important;
          border-color: #0d6e56 !important;
          color: #fff !important;
          border-radius: 10px !important;
          font-weight: 700 !important;
        }
        div.stButton > button[kind="secondary"],
        div.stButton > button[data-testid="baseButton-secondary"] {
          background: transparent !important;
          border: 1px solid #c9d5cc !important;
          color: #14211c !important;
          border-radius: 10px !important;
          font-weight: 700 !important;
        }
        div[data-testid="stForm"] {
          background: rgba(255,255,255,0.88);
          border: 1px solid rgba(201, 213, 204, 0.9);
          border-radius: 18px;
          padding: 1rem 1.1rem 0.4rem;
          box-shadow: 0 18px 50px rgba(20, 33, 28, 0.08);
        }

        /* ── Campos de datos bien visibles ── */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {
          background-color: #f7faf8 !important;
          color: #14211c !important;
          border: 2px solid #3d5249 !important;
          border-radius: 10px !important;
          min-height: 2.75rem !important;
          padding: 0.55rem 0.8rem !important;
          box-shadow: none !important;
        }
        [data-testid="stTextArea"] textarea,
        .stTextArea textarea {
          min-height: 5.5rem !important;
        }

        /* Contenedor BaseWeb (Streamlit envuelve el input) */
        [data-testid="stTextInput"] [data-baseweb="base-input"],
        [data-testid="stTextArea"] [data-baseweb="base-input"],
        [data-testid="stNumberInput"] [data-baseweb="base-input"],
        [data-testid="stTextInput"] > div > div,
        [data-testid="stTextArea"] > div > div,
        [data-testid="stNumberInput"] > div > div,
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"],
        div[data-baseweb="textarea"],
        div[data-baseweb="textarea"] > div {
          background-color: #f7faf8 !important;
          border: 2px solid #3d5249 !important;
          border-radius: 10px !important;
          outline: none !important;
        }

        /* Focus: borde verde fuerte */
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextInput"]:focus-within [data-baseweb="base-input"],
        [data-testid="stTextArea"]:focus-within [data-baseweb="base-input"],
        [data-testid="stNumberInput"]:focus-within [data-baseweb="base-input"],
        [data-testid="stTextInput"]:focus-within > div > div,
        [data-testid="stTextArea"]:focus-within > div > div,
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="base-input"]:focus-within,
        div[data-baseweb="textarea"] > div:focus-within {
          border-color: #0d6e56 !important;
          box-shadow: 0 0 0 3px rgba(13, 110, 86, 0.22) !important;
          background-color: #ffffff !important;
        }

        /* Quitar borde invisible / gris interno de Streamlit */
        [data-testid="stTextInput"] *,
        [data-testid="stTextArea"] *,
        [data-testid="stNumberInput"] * {
          border-color: inherit;
        }
        [data-testid="stTextInput"] div[data-baseweb="base-input"] input,
        [data-testid="stTextArea"] div[data-baseweb="base-input"] textarea {
          border: none !important;
          background: transparent !important;
        }

        code, .stCode code {
          font-family: "IBM Plex Mono", monospace !important;
        }
        [data-testid="stMetricValue"] {
          font-family: "IBM Plex Mono", monospace;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def nav_bar(page: str) -> None:
    st.markdown(
        f"""
        <div class="top-nav">
          <div class="brand">CertiPE</div>
          <div class="nav-links">{page}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_home() -> None:
    inst = certificates.institution_name()
    st.markdown(
        f"""
        <p class="eyebrow">{inst}</p>
        <h1 class="hero-title">Certificados firmados con Ed25519</h1>
        <p class="lead">
          Emite un certificado, fírmalo con la clave de la institución y compártelo.
          Cualquiera puede verificar si es auténtico o si lo alteraron.
        </p>
        """,
        unsafe_allow_html=True,
    )


def show_result_panel(result: dict, *, allow_revoke: bool = False) -> None:
    if result["ok"]:
        st.success(result["message"])
    else:
        st.error(result["message"])

    if not result.get("certificate"):
        return

    c = result["certificate"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Estado", c.get("status", "—"))
    m2.metric("Firma OK", str(result.get("signature_valid")))
    m3.metric("Hash OK", str(result.get("hash_valid")))
    st.write(
        {
            "código": c.get("id"),
            "titular": c.get("holder_name"),
            "documento": c.get("holder_doc"),
            "curso": c.get("course_title"),
            "institución": c.get("institution_name"),
            "emitido": c.get("issued_at"),
            "hash": c.get("payload_hash"),
        }
    )
    link = verify_url(c["id"])
    st.markdown("**Link de verificación**")
    st.code(link, language=None)
    try:
        st.image(pdf_cert.qr_png_bytes(link), caption="QR de validación", width=180)
    except Exception:
        pass
    try:
        pdf_bytes = pdf_cert.build_certificate_pdf(c, link)
        st.download_button(
            "Descargar PDF",
            data=pdf_bytes,
            file_name=f"{c['id']}.pdf",
            mime="application/pdf",
            key=f"pdf_{c['id']}_{allow_revoke}",
        )
    except Exception as e:  # noqa: BLE001
        st.warning(f"PDF no disponible: {e}")

    if allow_revoke and c.get("status") == "valid":
        if st.button("Revocar este certificado", type="secondary", key=f"rev_{c['id']}"):
            certificates.revoke(c["id"])
            st.warning("Revocado.")
            st.rerun()


def panel_pubkey() -> None:
    fp = crypto.public_key_fingerprint()
    pub = crypto.public_key_b64()
    st.markdown(
        f"""
        <div class="panel">
          <h2>Clave pública de la institución</h2>
          <p class="muted">Huella: <code>{fp}</code>. La privada nunca sale del servidor.</p>
          <div class="key-box">{pub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_recent() -> None:
    items = certificates.list_all()[:12]
    rows = ""
    if not items:
        rows = '<div class="list-row"><span class="list-meta">Aún no hay certificados.</span></div>'
    else:
        for c in items:
            status = c.get("status") or "valid"
            tag_cls = "tag revoked" if status == "revoked" else "tag"
            rows += (
                f'<div class="list-row">'
                f'<span class="list-id">{c.get("id")}</span>'
                f'<span class="list-meta">{c.get("holder_name")} · {c.get("course_title")}</span>'
                f'<span class="{tag_cls}">{status}</span>'
                f"</div>"
            )
    st.markdown(
        f"""
        <div class="panel">
          <h2>Últimos emitidos</h2>
          {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def foot() -> None:
    st.markdown(
        f'<p class="foot">MVP · Ed25519 · {APP_VERSION} · demo institucional</p>',
        unsafe_allow_html=True,
    )


# ── bootstrap ───────────────────────────────────────────────────────────────
bootstrap_secrets()
crypto.ensure_keys()
inject_web_look()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "inicio"

qp = st.query_params
codigo_qp = (qp.get("codigo") or qp.get("v") or "").strip().upper()
if (qp.get("public") or qp.get("mode") or "").lower() in {"1", "true", "validar", "validate"}:
    st.session_state["page"] = "validar_publico"
if qp.get("page") == "emitir":
    st.session_state["page"] = "emitir"
if qp.get("page") == "validar":
    st.session_state["page"] = "validar"

# Validación profunda por link (sin login)
if codigo_qp:
    nav_bar("Validar")
    st.markdown(
        f"""
        <p class="eyebrow">{certificates.institution_name()}</p>
        <h1 class="hero-title">Verificación pública</h1>
        <p class="lead">Código <code>{codigo_qp}</code></p>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        show_result_panel(certificates.validate(codigo_qp), allow_revoke=False)
    foot()
    st.stop()

usuario_cfg, clave_cfg, err_creds = cargar_credenciales()
login_requerido = usuario_cfg is not None and clave_cfg is not None

# Login solo para emitir / lista / admin — validar y ver inicio pueden ser mixtos
need_login_pages = {"emitir", "lista", "crypto"}
page = st.session_state["page"]

if (
    login_requerido
    and not st.session_state["autenticado"]
    and page in need_login_pages
):
    nav_bar("Acceso")
    st.markdown(
        f"""
        <p class="eyebrow">{certificates.institution_name()}</p>
        <h1 class="hero-title">Acceso institución</h1>
        <p class="lead">Inicia sesión para emitir certificados. La validación pública no pide clave.</p>
        """,
        unsafe_allow_html=True,
    )
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Validar código", use_container_width=True, type="secondary"):
            st.session_state["page"] = "validar_publico"
            st.rerun()
    with b2:
        if st.button("Volver al inicio", use_container_width=True, type="secondary"):
            st.session_state["page"] = "inicio"
            st.rerun()

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    if err_creds:
        st.error(err_creds)
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("Entrar", type="primary", use_container_width=True):
            if u.strip() == usuario_cfg and p == clave_cfg:
                st.session_state["autenticado"] = True
                st.session_state["page"] = "emitir"
                st.rerun()
            st.error("Usuario o clave incorrectos.")
    st.markdown("</div>", unsafe_allow_html=True)
    foot()
    st.stop()

# ── Páginas ─────────────────────────────────────────────────────────────────
if page == "inicio":
    nav_bar("Inicio")
    hero_home()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Emitir certificado", type="primary", use_container_width=True):
            st.session_state["page"] = "emitir"
            st.rerun()
    with c2:
        if st.button("Validar código", type="secondary", use_container_width=True):
            st.session_state["page"] = "validar_publico"
            st.rerun()

    if "seed_error" in st.session_state:
        st.error(f"Error en LLAVE_PRIVADA: {st.session_state['seed_error']}")

    panel_pubkey()
    panel_recent()

    # links admin
    if login_requerido and st.session_state["autenticado"]:
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("Lista", use_container_width=True):
                st.session_state["page"] = "lista"
                st.rerun()
        with a2:
            if st.button("Criptografía", use_container_width=True):
                st.session_state["page"] = "crypto"
                st.rerun()
        with a3:
            if st.button("Cerrar sesión", use_container_width=True):
                st.session_state["autenticado"] = False
                st.rerun()
    elif login_requerido:
        if st.button("Entrar como institución", type="secondary", use_container_width=True):
            st.session_state["page"] = "emitir"
            st.rerun()

    foot()

elif page in {"validar", "validar_publico"}:
    nav_bar("Validar")
    st.markdown(
        f"""
        <p class="eyebrow">{certificates.institution_name()}</p>
        <h1 class="hero-title">Validar certificado</h1>
        <p class="lead">Ingresa el código (ej. CERT-XXXX-XXXX-XXXX).</p>
        """,
        unsafe_allow_html=True,
    )
    codigo = st.text_input("Código", placeholder="CERT-....", label_visibility="collapsed")
    colv1, colv2 = st.columns(2)
    with colv1:
        go = st.button("Verificar firma", type="primary", use_container_width=True)
    with colv2:
        if st.button("← Inicio", type="secondary", use_container_width=True):
            st.session_state["page"] = "inicio"
            st.rerun()
    if go and codigo.strip():
        show_result_panel(
            certificates.validate(codigo.strip().upper()),
            allow_revoke=bool(st.session_state.get("autenticado")),
        )
    foot()

elif page == "emitir":
    nav_bar("Emitir")
    st.markdown(
        f"""
        <p class="eyebrow">{certificates.institution_name()}</p>
        <h1 class="hero-title">Emitir certificado</h1>
        <p class="lead">La institución firmará el documento con Ed25519.</p>
        """,
        unsafe_allow_html=True,
    )
    with st.form("emitir"):
        holder_name = st.text_input("Nombre del titulado", placeholder="Ana López")
        holder_doc = st.text_input("Documento (DNI / CE)", placeholder="12345678")
        course_title = st.text_input("Curso / programa", placeholder="Introducción a Python")
        course_hours = st.number_input("Horas (opcional)", min_value=0, max_value=10000, value=0)
        issued_by = st.text_input("Firmado por (opcional)", placeholder="Director académico")
        notes = st.text_area("Notas (opcional)", height=70)
        submitted = st.form_submit_button("Firmar y emitir", type="primary", use_container_width=True)
        if submitted:
            if not holder_name.strip() or not holder_doc.strip() or not course_title.strip():
                st.warning("Completa nombre, documento y curso.")
            else:
                rec = certificates.issue(
                    holder_name=holder_name,
                    holder_doc=holder_doc,
                    course_title=course_title,
                    course_hours=int(course_hours) or None,
                    issued_by=issued_by or None,
                    notes=notes or None,
                )
                st.session_state["last_cert"] = rec

    if st.button("← Inicio", type="secondary"):
        st.session_state["page"] = "inicio"
        st.rerun()

    if st.session_state.get("last_cert"):
        rec = st.session_state["last_cert"]
        st.success(f"Emitido: **{rec['id']}**")
        link = verify_url(rec["id"])
        st.code(link, language=None)
        ca, cb = st.columns([1, 2])
        with ca:
            try:
                st.image(pdf_cert.qr_png_bytes(link), width=160)
            except Exception as e:  # noqa: BLE001
                st.caption(str(e))
        with cb:
            try:
                pdf_bytes = pdf_cert.build_certificate_pdf(rec, link)
                st.download_button(
                    "Descargar PDF del certificado",
                    data=pdf_bytes,
                    file_name=f"{rec['id']}.pdf",
                    mime="application/pdf",
                    type="primary",
                    key="pdf_last",
                )
            except Exception as e:  # noqa: BLE001
                st.warning(f"PDF: {e}")
    foot()

elif page == "lista":
    nav_bar("Lista")
    st.markdown('<h1 class="hero-title">Certificados emitidos</h1>', unsafe_allow_html=True)
    if st.button("← Inicio", type="secondary"):
        st.session_state["page"] = "inicio"
        st.rerun()
    panel_recent()
    for c in certificates.list_all():
        with st.expander(f"{c['id']} · {c.get('status')}"):
            link = verify_url(c["id"])
            st.code(link, language=None)
            try:
                st.download_button(
                    "PDF",
                    data=pdf_cert.build_certificate_pdf(c, link),
                    file_name=f"{c['id']}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{c['id']}",
                )
            except Exception:
                pass
            if c.get("status") == "valid" and st.button("Revocar", key=f"r_{c['id']}"):
                certificates.revoke(c["id"])
                st.rerun()
    foot()

elif page == "crypto":
    nav_bar("Cripto")
    st.markdown('<h1 class="hero-title">Criptografía</h1>', unsafe_allow_html=True)
    if st.button("← Inicio", type="secondary"):
        st.session_state["page"] = "inicio"
        st.rerun()
    panel_pubkey()
    st.write(
        {
            "alg": "Ed25519",
            "fingerprint": crypto.public_key_fingerprint(),
            "public_key_hex": crypto.public_key_hex(),
            "app_version": APP_VERSION,
        }
    )
    foot()
