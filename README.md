# CertiPE — certificados firmados Ed25519 (Streamlit)

Python + Streamlit + secrets + Supabase + deploy en Streamlit Cloud.

## Qué hace

- **Emitir** certificados con firma Ed25519  
- **Validar** por código (`CERT-XXXX-...`)  
- **PDF + QR** de verificación  
- **Lista de alumnos** y export CSV/Excel desde Supabase  
- Verificación opcional con **motor_rust** (Rust)

## Arranque local

```bash
git clone https://github.com/dena0906zxfbjjluzz-max/certipe.git
cd certipe
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Si motor_rust falla, instala Rust y: maturin develop --release
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Seed Ed25519 (64 hex):

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Streamlit Cloud

1. Repo en GitHub · Main file: `app.py`  
2. Secrets: copiar `.streamlit/secrets.toml.example` con valores reales  
3. `packages.txt` instala `rustc`/`cargo` para compilar `motor_rust`

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `app.py` | UI Streamlit |
| `app/crypto.py` | Ed25519 (+ motor_rust) |
| `app/certificates.py` | Emitir / validar / revocar |
| `app/pdf_cert.py` | PDF certificado |
| `app/store.py` | Caché local del runtime |
| `src/lib.rs` | Motor Rust |
| `supabase/schema_certificados_certipe.sql` | Tabla Supabase |
| `.streamlit/secrets.toml.example` | Plantilla de secretos |
