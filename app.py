"""
CertiPE — Emisor / validador de certificados Ed25519.
Misma forma de trabajo que `validador`: Streamlit + secrets + GitHub Cloud.
"""

from __future__ import annotations

import os

import streamlit as st

from app import certificates, crypto

st.set_page_config(
    page_title="CertiPE · Certificados",
    page_icon="📜",
    layout="wide",
)


def _secret_get(*paths: str) -> str | None:
    """Lee secret anidado: ('credenciales','LLAVE_PRIVADA') o plano."""
    try:
        cur = st.secrets
        for p in paths:
            cur = cur[p]
        val = str(cur).strip()
        return val or None
    except Exception:
        return None


def bootstrap_secrets() -> None:
    """Carga LLAVE_PRIVADA e institución desde secrets (como validador)."""
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
        # Sin login configurado → modo abierto (dev / demo)
        return None, None, None


bootstrap_secrets()
crypto.ensure_keys()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Estilo sobrio (distinto del tema agro de validador, misma idea de app seria)
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

usuario_cfg, clave_cfg, err_creds = cargar_credenciales()
login_requerido = usuario_cfg is not None and clave_cfg is not None

# ── Login (igual patrón validador) ──────────────────────────────────────────
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
        "La pestaña **Validar** pública la publicamos sin login en un deploy aparte "
        "o desactiva usuario/clave en secrets para demo abierta."
    )
    st.stop()

# ── App ─────────────────────────────────────────────────────────────────────
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
                st.success(f"Emitido: **{rec['id']}**")
                st.code(rec["id"], language=None)
                st.json(
                    {
                        "id": rec["id"],
                        "holder_name": rec["holder_name"],
                        "course_title": rec["course_title"],
                        "payload_hash": rec["payload_hash"],
                        "signature": rec["signature"],
                        "status": rec["status"],
                    }
                )

with tab_validar:
    st.subheader("Validar certificado")
    codigo = st.text_input("Código", placeholder="CERT-XXXX-XXXX-XXXX", key="codigo_val")
    if st.button("Verificar firma", type="primary") or codigo:
        cid = (codigo or "").strip().upper()
        if cid:
            result = certificates.validate(cid)
            if result["ok"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
            if result.get("certificate"):
                c = result["certificate"]
                m1, m2, m3 = st.columns(3)
                m1.metric("Estado", c.get("status", "—"))
                m2.metric("Firma OK", str(result.get("signature_valid")))
                m3.metric("Hash OK", str(result.get("hash_valid")))
                st.write(
                    {
                        "titular": c.get("holder_name"),
                        "documento": c.get("holder_doc"),
                        "curso": c.get("course_title"),
                        "institución": c.get("institution_name"),
                        "emitido": c.get("issued_at"),
                        "hash": c.get("payload_hash"),
                    }
                )
            if result.get("certificate"):
                if st.button("Revocar este certificado", type="secondary"):
                    certificates.revoke(cid)
                    st.warning("Certificado revocado.")
                    st.rerun()

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
        }
    )
    st.markdown(
        """
**Streamlit Cloud (como validador)**  
Settings → Secrets:

```toml
[credenciales]
usuario = "admin"
clave = "cambia-esto"
LLAVE_PRIVADA = "64_caracteres_hex"
nombre_institucion = "Tu Academia"
```

Generar seed local:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
"""
    )

if login_requerido and st.session_state["autenticado"]:
    if st.sidebar.button("Cerrar sesión"):
        st.session_state["autenticado"] = False
        st.rerun()
