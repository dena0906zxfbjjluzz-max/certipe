# CertiPE — certificados firmados Ed25519 (Streamlit)

Misma forma de trabajo que [validador](https://github.com/dena0906zxfbjjluzz-max/validador):  
Python + Streamlit + secrets + deploy en Streamlit Cloud desde GitHub.

## Qué hace

- **Emitir** certificados de curso con firma Ed25519 de la institución  
- **Validar** por código (`CERT-XXXX-...`): auténtico / alterado / revocado  
- **PDF + QR** de verificación pública  
- **Validación sin login:** `?codigo=CERT-...` o `?public=validar`  
- **Clave pública** visible; la privada solo en secrets  

No reemplaza IOFE / Firma Perú del Estado. Sirve para academias, bootcamps y certificados privados.

## Arranque local (como validador)

```bash
git clone https://github.com/dena0906zxfbjjluzz-max/certipe.git
cd certipe
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# editar LLAVE_PRIVADA, usuario y clave
streamlit run app.py
```

Generar seed Ed25519 (64 hex):

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Streamlit Cloud

1. Sube este repo a GitHub  
2. [share.streamlit.io](https://share.streamlit.io) → New app  
3. Main file: `app.py`  
4. Secrets → pega el contenido de `.streamlit/secrets.toml.example` (con valores reales)

## Estructura

| Archivo | Rol |
|---------|-----|
| `app.py` | UI Streamlit |
| `app/crypto.py` | Ed25519 (cryptography / PyNaCl) |
| `app/certificates.py` | Emitir / validar / revocar |
| `app/store.py` | Almacenamiento JSON local |
| `.streamlit/secrets.toml.example` | Plantilla de secretos |

## Nota sobre datos en la nube

El JSON en `data/` es local al contenedor: en Streamlit Cloud puede reiniciarse.  
Para producción, conviene Supabase (igual idea que validador). MVP ok para demos.
