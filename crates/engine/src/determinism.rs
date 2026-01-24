//! Determinism utilities for stable primitives
//!
//! This module provides deterministic utilities that can be used to validate
//! determinism in the engine. These are stable primitives that will remain
//! unchanged across versions.

use serde::Serialize;
use sha2::{Digest, Sha256};

/// Compute a stable SHA-256 hash from bytes
///
/// This function takes raw bytes and returns their SHA-256 hash as a hex string.
/// The output is deterministic and stable across all platforms and runs.
///
/// # Examples
///
/// ```
/// use engine::stable_hash_bytes;
///
/// let data = b"Hello, World!";
/// let hash = stable_hash_bytes(data);
/// assert_eq!(hash, "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f");
/// ```
pub fn stable_hash_bytes(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    let result = hasher.finalize();
    hex::encode(result)
}

/// Serialize a value to canonical JSON bytes and hash it
///
/// This function serializes a value to JSON (deterministic ordering) and
/// computes its SHA-256 hash. This is useful for hashing structured data.
///
/// # Examples
///
/// ```
/// use engine::canonical_json_hash;
/// use serde::Serialize;
///
/// #[derive(Serialize)]
/// struct Data {
///     name: String,
///     value: i32,
/// }
///
/// let data = Data { name: "test".to_string(), value: 42 };
/// let hash = canonical_json_hash(&data).unwrap();
/// // The hash is deterministic for the same struct
/// assert_eq!(hash.len(), 64); // SHA-256 produces 64 hex chars
/// ```
pub fn canonical_json_hash<T: Serialize>(data: &T) -> Result<String, serde_json::Error> {
    let json_bytes = serde_json::to_vec(data)?;
    Ok(stable_hash_bytes(&json_bytes))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stable_hash_bytes_deterministic() {
        let data = b"test data";
        let hash1 = stable_hash_bytes(data);
        let hash2 = stable_hash_bytes(data);
        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_stable_hash_bytes_known_value() {
        // Known SHA-256 hash for "Hello, World!"
        let data = b"Hello, World!";
        let hash = stable_hash_bytes(data);
        assert_eq!(
            hash,
            "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        );
    }

    #[test]
    fn test_canonical_json_hash_deterministic() {
        use serde::Serialize;

        #[derive(Serialize)]
        struct TestData {
            field1: String,
            field2: i32,
        }

        let data = TestData {
            field1: "value".to_string(),
            field2: 123,
        };

        let hash1 = canonical_json_hash(&data).unwrap();
        let hash2 = canonical_json_hash(&data).unwrap();
        assert_eq!(hash1, hash2);
    }
}
