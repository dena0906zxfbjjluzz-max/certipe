# CertiPE

Certificados de cursos firmados con **Ed25519**, emisión y validación pública,
PDF + QR, lista de alumnos en **Supabase**. UI con **Streamlit**.

> No reemplaza IOFE / Firma Perú. Sirve para academias, bootcamps y certificados privados.

---

## Demo rápida (prueba automática)

Sin abrir la web, verifica emitir → validar → fraude → PDF:

```bash
cd certipe
python3 -m venv .venv && source .venv/bin/activate   # primera vez
pip install -r requirements.txt
python demo_prueba.py
```

Salida esperada: `=== Demo OK ===` y marcas `✓` en cada paso.

Opcional (motor Rust nativo):

```bash
# requiere rustc + cargo (packages.txt en Streamlit Cloud)
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop --release
python demo_prueba.py   # debe mostrar motor_rust disponible: True
```

---

## Arranque de la app

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editar: LLAVE_PRIVADA (64 hex), usuario, clave, SUPABASE_*
streamlit run app.py
```

Generar seed de institución:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Recorrido demo en la web

1. **Inicio** → clave pública + últimos emitidos (desde Supabase).  
2. **Emitir certificado** → login institución → completar formulario → PDF y link.  
3. **Validar código** → pegar `CERT-XXXX-XXXX-XXXX` → ver autenticidad / motor.  
4. **Lista** (logueado) → buscar alumnos, exportar CSV o Excel.  
5. Link público: `https://tu-app.streamlit.app/?codigo=CERT-...`

---

## Streamlit Cloud

| Paso | Acción |
|------|--------|
| 1 | Repo en GitHub; Main file: `app.py` |
| 2 | **Secrets** = contenido de `.streamlit/secrets.toml.example` (valores reales) |
| 3 | `packages.txt` instala `rustc`/`cargo` para `motor_rust` |
| 4 | Reboot tras el primer deploy si falla el build de Rust |

Tabla en Supabase (SQL Editor):

```bash
# archivo en el repo
supabase/schema_certificados_certipe.sql
```

---

## Secrets (resumen)

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."   # anon o service_role

[credenciales]
usuario = "admin"
clave = "tu-clave"
LLAVE_PRIVADA = "64_caracteres_hex"
nombre_institucion = "Academia Demo Perú"
```

---

## Estructura

```
app.py                 # UI Streamlit
app/crypto.py          # Ed25519 + motor_rust
app/certificates.py    # emitir / validar / revocar
app/pdf_cert.py        # PDF A4 horizontal
app/store.py           # caché JSON del runtime
src/lib.rs             # verificación Ed25519 en Rust
demo_prueba.py         # prueba demo local
supabase/schema_….sql  # tabla certificados_certipe
requirements.txt
packages.txt           # rustc, cargo (Cloud)
```

---

## Notas

- **Últimos emitidos** y **Lista** leen solo `public.certificados_certipe`.  
- La firma se valida con `motor_rust` si está compilado; si no, `cryptography`.  
- En Cloud el JSON local se reinicia: la fuente durable es **Supabase**.
