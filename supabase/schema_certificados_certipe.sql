-- Completar public.certificados_certipe para CertiPE
-- Ejecutar en Supabase → SQL Editor → Run

-- Hash SHA-256 del payload firmado
alter table public.certificados_certipe
  add column if not exists document_hash text;

-- Firma Ed25519 (proofValue)
alter table public.certificados_certipe
  add column if not exists proof_value text;

-- Asegurar default en fecha_emision si no lo tiene
alter table public.certificados_certipe
  alter column fecha_emision set default now();

-- (Opcional) código CERT-XXXX para enlazar con la app
alter table public.certificados_certipe
  add column if not exists codigo_cert text;

comment on column public.certificados_certipe.document_hash is 'SHA-256 del JSON canónico del certificado';
comment on column public.certificados_certipe.proof_value is 'Firma Ed25519 (base64url)';
