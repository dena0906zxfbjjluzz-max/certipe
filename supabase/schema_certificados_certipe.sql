-- Recrear tabla completa para CertiPE (borrar datos de prueba)
-- Supabase → SQL Editor → Run

DROP TABLE IF EXISTS public.certificados_certipe;

CREATE TABLE public.certificados_certipe (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    fecha_emision TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    codigo_cert TEXT UNIQUE,
    dni_alumno TEXT NOT NULL,
    nombre_alumno TEXT NOT NULL,
    curso TEXT NOT NULL,
    document_hash TEXT NOT NULL UNIQUE,
    proof_value TEXT NOT NULL
);

-- Importante: sin RLS para que Streamlit (anon key) pueda insertar en el MVP
ALTER TABLE public.certificados_certipe DISABLE ROW LEVEL SECURITY;

-- Comprobar columnas
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'certificados_certipe'
ORDER BY ordinal_position;
