//! motor_rust — verificación Ed25519 nativa (PyO3 + ed25519-dalek).

use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use pyo3::prelude::*;

/// Decodifica un string hex flexible (espacios, opcional `0x`).
fn decode_hex(s: &str) -> Option<Vec<u8>> {
    let mut limpio: String = s.chars().filter(|c| !c.is_whitespace()).collect();
    if limpio.starts_with("0x") || limpio.starts_with("0X") {
        limpio = limpio[2..].to_string();
    }
    if limpio.is_empty() || limpio.len() % 2 != 0 {
        return None;
    }
    let mut out = Vec::with_capacity(limpio.len() / 2);
    let bytes = limpio.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let hi = from_hex_nibble(bytes[i])?;
        let lo = from_hex_nibble(bytes[i + 1])?;
        out.push((hi << 4) | lo);
        i += 2;
    }
    Some(out)
}

fn from_hex_nibble(b: u8) -> Option<u8> {
    match b {
        b'0'..=b'9' => Some(b - b'0'),
        b'a'..=b'f' => Some(b - b'a' + 10),
        b'A'..=b'F' => Some(b - b'A' + 10),
        _ => None,
    }
}

/// Valida una firma Ed25519 a velocidad nativa.
///
/// - `public_key_hex`: clave pública raw (32 bytes) en hex (64 chars)
/// - `signature_hex`: firma (64 bytes) en hex (128 chars)
/// - `message_hash_hex`: mensaje firmado en hex (p. ej. hash SHA-256 → 32 bytes / 64 chars)
///
/// Devuelve `true` solo si la firma es válida; hex inválido o error de longitud → `false`.
#[pyfunction]
fn verificar_firma_rust(
    public_key_hex: &str,
    signature_hex: &str,
    message_hash_hex: &str,
) -> bool {
    let Some(pk_bytes) = decode_hex(public_key_hex) else {
        return false;
    };
    let Some(sig_bytes) = decode_hex(signature_hex) else {
        return false;
    };
    let Some(msg_bytes) = decode_hex(message_hash_hex) else {
        return false;
    };

    if pk_bytes.len() != 32 || sig_bytes.len() != 64 {
        return false;
    }

    let pk_arr: [u8; 32] = match pk_bytes.as_slice().try_into() {
        Ok(a) => a,
        Err(_) => return false,
    };
    let sig_arr: [u8; 64] = match sig_bytes.as_slice().try_into() {
        Ok(a) => a,
        Err(_) => return false,
    };

    let verifying_key = match VerifyingKey::from_bytes(&pk_arr) {
        Ok(vk) => vk,
        Err(_) => return false,
    };
    let signature = Signature::from_bytes(&sig_arr);

    verifying_key.verify(&msg_bytes, &signature).is_ok()
}

/// Módulo Python: `import motor_rust`
#[pymodule]
fn motor_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(verificar_firma_rust, m)?)?;
    Ok(())
}
