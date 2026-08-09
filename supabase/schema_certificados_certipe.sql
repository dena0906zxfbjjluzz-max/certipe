-- Columnas CertiPE en public.certificados_certipe
-- Ejecutar en Supabase → SQL Editor → Run

alter table public.certificados_certipe
  add column if not exists document_hash text;

alter table public.certificados_certipe
  add column if not exists proof_value text;

-- Código del certificado (CERT-XXXX-XXXX-XXXX)
alter table public.certificados_certipe
  add column if not exists codigo_cert text;

-- Índice único para buscar por código
create unique index if not exists certificados_certipe_codigo_cert_uidx
  on public.certificados_certipe (codigo_cert)
  where codigo_cert is not null;

alter table public.certificados_certipe
  alter column fecha_emision set default now();

comment on column public.certificados_certipe.codigo_cert is 'Código público CERT-XXXX usado en validación';
comment on column public.certificados_certipe.document_hash is 'SHA-256 del JSON canónico';
comment on column public.certificados_certipe.proof_value is 'Firma Ed25519 (base64url)';
