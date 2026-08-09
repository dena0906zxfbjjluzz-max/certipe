"""
CertiPE — Emisor / validador de certificados Ed25519.
Streamlit + secrets + PDF + QR + validación pública (UI tipo ventana).
"""

from __future__ import annotations

import os
from urllib.parse import quote

import streamlit as st

from app import certificates, crypto
from app import pdf_cert

APP_VERSION = "1.1 · PDF · QR · validación pública"

st.set_page_config(
    page_title="CertiPE · Certificados",
    page_icon="📜",
    layout="wide",
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


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700;9..40,800&family=IBM+Plex+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] { font-family: "DM Sans", sans-serif; }
        .block-container { padding-top: 1.2rem; max-width: 980px; }
        code, .stCode { font-family: "IBM Plex Mono", monospace !important; }
        div[data-testid="stMetricValue"] { font-family: "IBM Plex Mono", monospace; }

        .hero-card {
            background: linear-gradient(135deg, #0d6e56 0%, #145a4a 55%, #1a3d34 100%);
            color: #f4faf7;
            border-radius: 18px;
            padding: 1.4rem 1.5rem 1.5rem;
            margin: 0 0 1.2rem 0;
            box-shadow: 0 14px 40px rgba(13, 110, 86, 0.28);
            border: 1px solid rgba(255,255,255,0.12);
        }
        .hero-card h1 {
            margin: 0 0 0.35rem 0;
            font-size: 1.85rem;
            letter-spacing: -0.03em;
            color: #fff !important;
        }
        .hero-card p {
            margin: 0.25rem 0;
            opacity: 0.92;
            color: #e8f5ef !important;
        }
        .hero-card .chip {
            display: inline-block;
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 999px;
            padding: 0.18rem 0.7rem;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .window-card {
            background: #ffffff;
            border: 1px solid #cfdcd5;
            border-radius: 16px;
            padding: 0;
            margin: 0.4rem 0 1.2rem 0;
            box-shadow: 0 16px 48px rgba(20, 33, 28, 0.10);
            overflow: hidden;
        }
        .window-bar {
            background: #eef4f0;
            border-bottom: 1px solid #d5e0da;
            padding: 0.55rem 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.82rem;
            font-weight: 700;
            color: #3d5249;
        }
        .dot {
            width: 10px; height: 10px; border-radius: 50%; display: inline-block;
        }
        .dot.r { background: #e35d5d; }
        .dot.y { background: #e3b35d; }
        .dot.g { background: #4caf7a; }
        .window-body {
            padding: 1.1rem 1.2rem 1.25rem;
        }
        .window-body h2 {
            margin: 0 0 0.35rem 0;
            font-size: 1.35rem;
            color: #14211c;
            letter-spacing: -0.02em;
        }
        .window-body .muted {
            color: #5b6b63;
            margin: 0 0 0.9rem 0;
            font-size: 0.95rem;
        }
        .welcome-box {
            background: #e8f6ef;
            border: 1px solid #b7 rec8c5;
            border-left: 5px solid #0d6e56;
            border-radius: 12px;
            padding: 0.95rem 1.1rem;
            margin: 0 0 1rem 0;
        }
        .welcome-box strong { color: #0d6e56; }
        .welcome-box p { margin: 0.25rem 0 0 0; color: #2f463d; font-size: 0.95rem; }
        .version-tag {
            font-size: 0.75rem;
            color: #6b7c74;
            margin-top: 0.15rem;
        }
        </style>
        """.replace("#b7 rec8c5", "#b7d8c5"),
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
        if st.button("Revocar este certificado", type="secondary", key=f"rev_panel_{c['id']}"):
            certificates.revoke(c["id"])
            st.warning("Certificado revocado.")
            st.rerun()


def window_open(title: str, muted: str = "") -> None:
    st.markdown(
        f"""
        <div class="window-card">
          <div class="window-bar">
            <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
            <span style="margin-left:0.4rem">{title}</span>
          </div>
          <div class="window-body">
            <h2>{title}</h2>
            <p class="muted">{muted}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_public_validate(prefill: str = "", *, standalone: bool = True) -> None:
    if standalone:
        st.markdown(
            f"""
            <div class="hero-card">
              <div class="chip">Verificación pública · sin login</div>
              <h1>CertiPE</h1>
              <p>{certificates.institution_name()}</p>
              <p class="version-tag" style="color:#cfe8dc!important;opacity:0.9">{APP_VERSION}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="window-card">
          <div class="window-bar">
            <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
            <span style="margin-left:0.4rem">Validar certificado</span>
          </div>
          <div class="window-body">
            <div class="welcome-box">
              <strong>Bienvenido</strong>
              <p>Ingresa el código del certificado (ej. CERT-XXXX-XXXX-XXXX).
              Verificamos firma Ed25519 e integridad del documento.</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("Código de verificación")
        codigo = st.text_input(
            "Código del certificado",
            value=prefill,
            placeholder="CERT-XXXX-XXXX-XXXX",
            key="public_codigo",
            label_visibility="collapsed",
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            go = st.button("Verificar firma", type="primary", use_container_width=True)
        with col2:
            if not standalone and st.button("Volver al panel", use_container_width=True):
                st.session_state["modo_publico"] = False
                st.query_params.clear()
                st.rerun()

        if go or prefill:
            cid = (codigo or prefill or "").strip().upper()
            if cid:
                st.divider()
                show_result_panel(certificates.validate(cid), allow_revoke=False)


bootstrap_secrets()
crypto.ensure_keys()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "modo_publico" not in st.session_state:
    st.session_state["modo_publico"] = False

inject_styles()

# ── Validación pública ──────────────────────────────────────────────────────
qp = st.query_params
codigo_qp = (qp.get("codigo") or qp.get("v") or "").strip().upper()
public_mode = (qp.get("public") or qp.get("mode") or "").lower() in {
    "1",
    "true",
    "validar",
    "validate",
}
if public_mode:
    st.session_state["modo_publico"] = True

if codigo_qp:
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="chip">Resultado de verificación</div>
          <h1>CertiPE</h1>
          <p>{certificates.institution_name()}</p>
          <p>Código: <strong style="color:#fff">{codigo_qp}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        show_result_panel(certificates.validate(codigo_qp), allow_revoke=False)
    st.stop()

if st.session_state["modo_publico"] or public_mode:
    page_public_validate(standalone=True)
    st.stop()

usuario_cfg, clave_cfg, err_creds = cargar_credenciales()
login_requerido = usuario_cfg is not None and clave_cfg is not None

# ── Login ───────────────────────────────────────────────────────────────────
if login_requerido and not st.session_state["autenticado"]:
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="chip">CertiPE · {APP_VERSION}</div>
          <h1>Panel de la institución</h1>
          <p>{certificates.institution_name()}</p>
          <p>Emite certificados firmados con Ed25519 y compártelos con QR o PDF.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Cuadro bienvenida + acceso a validación pública
    st.markdown(
        """
        <div class="window-card">
          <div class="window-bar">
            <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
            <span style="margin-left:0.4rem">Validación pública</span>
          </div>
          <div class="window-body">
            <div class="welcome-box">
              <strong>¿Solo quieres comprobar un certificado?</strong>
              <p>No necesitas usuario ni clave. Abre el validador público y pega el código CERT-…</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Abrir validación pública", type="primary", use_container_width=True):
        st.session_state["modo_publico"] = True
        st.query_params["public"] = "validar"
        st.rerun()

    st.markdown("")
    with st.container(border=True):
        st.subheader("Acceso institución")
        if err_creds:
            st.error(err_creds)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            ok = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            if ok:
                if u.strip() == usuario_cfg and p == clave_cfg:
                    st.session_state["autenticado"] = True
                    st.session_state["modo_publico"] = False
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos.")
    st.stop()

# ── App privada ─────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="hero-card">
      <div class="chip">CertiPE · {APP_VERSION}</div>
      <h1>Panel institución</h1>
      <p>{certificates.institution_name()} · firmas Ed25519 · huella {crypto.public_key_fingerprint()}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Banner validación pública tipo ventana (visible, no solo sidebar)
st.markdown(
    """
    <div class="window-card">
      <div class="window-bar">
        <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
        <span style="margin-left:0.4rem">Validación pública</span>
      </div>
      <div class="window-body">
        <div class="welcome-box">
          <strong>Comparte el validador con empresas / alumnos</strong>
          <p>Pueden verificar autenticidad sin entrar al panel. El link usa
          <code>?public=validar</code> o <code>?codigo=CERT-…</code>.</p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
bp1, bp2 = st.columns([1, 1])
with bp1:
    if st.button("Abrir validación pública", type="primary", use_container_width=True, key="btn_pub_main"):
        st.session_state["modo_publico"] = True
        st.query_params["public"] = "validar"
        st.rerun()
with bp2:
    pub_link = f"{app_base_url()}/?public=validar" if app_base_url() else "?public=validar"
    st.code(pub_link, language=None)

if "seed_error" in st.session_state:
    st.error(f"Error en LLAVE_PRIVADA: {st.session_state['seed_error']}")

tab_emitir, tab_validar, tab_lista, tab_crypto = st.tabs(
    ["Emitir", "Validar", "Lista", "Criptografía"]
)

with tab_emitir:
    with st.container(border=True):
        st.subheader("Emitir certificado")
        with st.form("emitir"):
            c1, c2 = st.columns(2)
            with c1:
                holder_name = st.text_input("Nombre del titulado", placeholder="Ana López")
                holder_doc = st.text_input("Documento (DNI / CE)", placeholder="71234567")
                course_title = st.text_input("Curso / programa", placeholder="Introducción a Python")
            with c2:
                course_hours = st.number_input(
                    "Horas (0 = no indicar)", min_value=0, max_value=10000, value=0
                )
                issued_by = st.text_input("Firmado por", placeholder="Director académico")
                notes = st.text_area("Notas", height=80)
            submit = st.form_submit_button("Firmar y emitir", type="primary")
            if submit:
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

    if st.session_state.get("last_cert"):
        rec = st.session_state["last_cert"]
        st.markdown(
            """
            <div class="window-card">
              <div class="window-bar">
                <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
                <span style="margin-left:0.4rem">Certificado emitido</span>
              </div>
              <div class="window-body">
                <div class="welcome-box">
                  <strong>Listo</strong>
                  <p>Descarga el PDF, copia el link o muestra el QR al alumno.</p>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.success(f"Emitido: **{rec['id']}**")
        link = verify_url(rec["id"])
        st.markdown("**Link de verificación**")
        st.code(link, language=None)
        col_a, col_b = st.columns([1, 2])
        with col_a:
            try:
                st.image(pdf_cert.qr_png_bytes(link), width=180)
            except Exception as e:  # noqa: BLE001
                st.caption(f"QR: {e}")
        with col_b:
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
                st.warning(f"PDF no disponible: {e}")
            st.json(
                {
                    "id": rec["id"],
                    "holder_name": rec["holder_name"],
                    "course_title": rec["course_title"],
                    "payload_hash": rec["payload_hash"],
                    "status": rec["status"],
                }
            )

with tab_validar:
    with st.container(border=True):
        st.subheader("Validar certificado (panel)")
        codigo = st.text_input("Código", placeholder="CERT-XXXX-XXXX-XXXX", key="codigo_val")
        if st.button("Verificar firma", type="primary", key="btn_val") or codigo:
            cid = (codigo or "").strip().upper()
            if cid:
                show_result_panel(certificates.validate(cid), allow_revoke=True)

with tab_lista:
    st.subheader("Certificados emitidos")
    items = certificates.list_all()
    if not items:
        st.info("Aún no hay certificados. Emite uno en la pestaña Emitir.")
    else:
        for c in items:
            with st.expander(f"{c['id']} · {c['holder_name']} · {c.get('status')}"):
                st.write(
                    {
                        "curso": c.get("course_title"),
                        "documento": c.get("holder_doc"),
                        "emitido": c.get("issued_at"),
                        "hash": c.get("payload_hash"),
                    }
                )
                link = verify_url(c["id"])
                st.code(link, language=None)
                b1, b2 = st.columns(2)
                with b1:
                    try:
                        pdf_bytes = pdf_cert.build_certificate_pdf(c, link)
                        st.download_button(
                            "PDF",
                            data=pdf_bytes,
                            file_name=f"{c['id']}.pdf",
                            mime="application/pdf",
                            key=f"pdf_list_{c['id']}",
                        )
                    except Exception:
                        pass
                with b2:
                    if c.get("status") == "valid" and st.button("Revocar", key=f"rev_{c['id']}"):
                        certificates.revoke(c["id"])
                        st.rerun()

with tab_crypto:
    with st.container(border=True):
        st.subheader("Clave pública de la institución")
        st.caption("Cualquiera puede usarla para verificar firmas. La privada va en secrets.")
        st.code(crypto.public_key_b64(), language=None)
        st.write(
            {
                "alg": "Ed25519",
                "fingerprint": crypto.public_key_fingerprint(),
                "public_key_hex": crypto.public_key_hex(),
                "app_version": APP_VERSION,
                "public_base_url": app_base_url() or "(auto Host)",
            }
        )

with st.sidebar:
    st.markdown(f"**CertiPE** `{APP_VERSION}`")
    if login_requerido and st.session_state["autenticado"]:
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state["autenticado"] = False
            st.rerun()
    if st.button("Validación pública", type="primary", use_container_width=True, key="side_pub"):
        st.session_state["modo_publico"] = True
        st.query_params["public"] = "validar"
        st.rerun()
