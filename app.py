"""
CertiPE — Emisor / validador de certificados Ed25519.
Streamlit + secrets + PDF + QR + validación pública.
"""

from __future__ import annotations

import os
from urllib.parse import quote

import streamlit as st

from app import certificates, crypto
from app import pdf_cert

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
    """URL pública de la app (para QR y links)."""
    explicit = (
        _secret_get("PUBLIC_BASE_URL")
        or _secret_get("credenciales", "PUBLIC_BASE_URL")
        or os.environ.get("PUBLIC_BASE_URL")
    )
    if explicit:
        return explicit.rstrip("/")
    try:
        # Streamlit Cloud / proxy
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
    # Fallback relativo (al escanear en la misma app)
    return f"?codigo={quote(cert_id)}"


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
    st.markdown(f"**Link de verificación:** `{link}`")
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


def page_public_validate(prefill: str = "") -> None:
    st.title("Validar certificado")
    st.caption(f"{certificates.institution_name()} · verificación pública (sin login)")
    codigo = st.text_input(
        "Código del certificado",
        value=prefill,
        placeholder="CERT-XXXX-XXXX-XXXX",
        key="public_codigo",
    )
    if st.button("Verificar firma", type="primary") or prefill:
        cid = (codigo or prefill or "").strip().upper()
        if cid:
            show_result_panel(certificates.validate(cid), allow_revoke=False)


bootstrap_secrets()
crypto.ensure_keys()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700&family=IBM+Plex+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { font-family: "DM Sans", sans-serif; }
    .block-container { padding-top: 1.4rem; max-width: 980px; }
    code, .stCode { font-family: "IBM Plex Mono", monospace !important; }
    div[data-testid="stMetricValue"] { font-family: "IBM Plex Mono", monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Validación pública (sin login) ──────────────────────────────────────────
qp = st.query_params
codigo_qp = (qp.get("codigo") or qp.get("v") or "").strip().upper()
public_mode = (qp.get("public") or qp.get("mode") or "").lower() in {"1", "true", "validar", "validate"}

if codigo_qp:
    st.title("CertiPE · Verificación")
    st.caption(certificates.institution_name())
    show_result_panel(certificates.validate(codigo_qp), allow_revoke=False)
    st.stop()

if public_mode:
    page_public_validate()
    st.stop()

usuario_cfg, clave_cfg, err_creds = cargar_credenciales()
login_requerido = usuario_cfg is not None and clave_cfg is not None

# ── Login ───────────────────────────────────────────────────────────────────
if login_requerido and not st.session_state["autenticado"]:
    st.title("CertiPE")
    st.caption(certificates.institution_name())
    st.subheader("Acceso institución")
    if err_creds:
        st.error(err_creds)
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        ok = st.form_submit_button("Entrar", type="primary")
        if ok:
            if u.strip() == usuario_cfg and p == clave_cfg:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Usuario o clave incorrectos.")
    st.info(
        "¿Solo validar un certificado? Abre el link público "
        "`?public=validar` o `?codigo=CERT-XXXX` (no requiere clave)."
    )
    st.stop()

# ── App privada ─────────────────────────────────────────────────────────────
st.title("CertiPE")
st.caption(
    f"{certificates.institution_name()} · firmas Ed25519 · "
    f"huella `{crypto.public_key_fingerprint()}`"
)

if "seed_error" in st.session_state:
    st.error(f"Error en LLAVE_PRIVADA: {st.session_state['seed_error']}")

tab_emitir, tab_validar, tab_lista, tab_crypto = st.tabs(
    ["Emitir", "Validar", "Lista", "Criptografía"]
)

with tab_emitir:
    st.subheader("Emitir certificado")
    with st.form("emitir"):
        c1, c2 = st.columns(2)
        with c1:
            holder_name = st.text_input("Nombre del titulado", placeholder="Ana López")
            holder_doc = st.text_input("Documento (DNI / CE)", placeholder="71234567")
            course_title = st.text_input("Curso / programa", placeholder="Introducción a Python")
        with c2:
            course_hours = st.number_input("Horas (0 = no indicar)", min_value=0, max_value=10000, value=0)
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

    # Resultado fuera del form (PDF / QR / link)
    if st.session_state.get("last_cert"):
        rec = st.session_state["last_cert"]
        st.success(f"Emitido: **{rec['id']}**")
        link = verify_url(rec["id"])
        st.markdown("**Link de verificación (cópialo o usa el QR):**")
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
    st.subheader("Validar certificado")
    codigo = st.text_input("Código", placeholder="CERT-XXXX-XXXX-XXXX", key="codigo_val")
    if st.button("Verificar firma", type="primary", key="btn_val") or codigo:
        cid = (codigo or "").strip().upper()
        if cid:
            show_result_panel(certificates.validate(cid), allow_revoke=True)

with tab_lista:
    st.subheader("Certificados emitidos")
    items = certificates.list_all()
    if not items:
        st.info("Aún no hay certificados.")
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
    st.subheader("Clave pública de la institución")
    st.caption("Cualquiera puede usarla para verificar firmas. La privada va en secrets.")
    st.code(crypto.public_key_b64(), language=None)
    st.write(
        {
            "alg": "Ed25519",
            "fingerprint": crypto.public_key_fingerprint(),
            "public_key_hex": crypto.public_key_hex(),
            "public_base_url": app_base_url() or "(auto Host / define PUBLIC_BASE_URL en secrets)",
        }
    )
    st.markdown(
        """
**Validación pública (sin login)**  
- `https://tu-app.streamlit.app/?codigo=CERT-XXXX`  
- `https://tu-app.streamlit.app/?public=validar`  

Opcional en secrets:
```toml
PUBLIC_BASE_URL = "https://tu-app.streamlit.app"
```
"""
    )

if login_requerido and st.session_state["autenticado"]:
    if st.sidebar.button("Cerrar sesión"):
        st.session_state["autenticado"] = False
        st.rerun()
    st.sidebar.markdown("[Validación pública](?public=validar)")
