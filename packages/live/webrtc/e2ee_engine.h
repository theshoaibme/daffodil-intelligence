#ifndef DI_E2EE_ENGINE_H
#define DI_E2EE_ENGINE_H

#include <cstdint>
#include <cstring>
#include <array>
#include <vector>
#include <optional>
#include <memory>
#include <atomic>
#include <functional>

// OpenSSL includes
#include <openssl/evp.h>
#include <openssl/ec.h>
#include <openssl/ecdsa.h>
#include <openssl/ecdh.h>
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <openssl/hmac.h>

namespace di {
namespace crypto {

// ============================================================================
// CONSTANTS
// ============================================================================

constexpr size_t AES_256_KEY_SIZE = 32;        // 256 bits
constexpr size_t AES_GCM_IV_SIZE = 12;          // 96 bits (recommended)
constexpr size_t AES_GCM_TAG_SIZE = 16;         // 128 bits
constexpr size_t ECDH_KEY_SIZE = 32;            // P-256 generates 32 bytes
constexpr size_t PUBLIC_KEY_SIZE = 65;           // Uncompressed P-256

constexpr size_t MAX_FRAME_SIZE = 2 * 1024 * 1024;  // 2MB max
constexpr size_t ENCRYPTION_OVERHEAD = AES_GCM_IV_SIZE + AES_GCM_TAG_SIZE;

// ============================================================================
// ERROR CODES
// ============================================================================

enum class CryptoResult : int {
    SUCCESS = 0,
    INVALID_KEY = -1,
    INVALID_IV = -2,
    ENCRYPTION_FAILED = -3,
    DECRYPTION_FAILED = -4,
    KEY_EXCHANGE_FAILED = -5,
    ALLOCATION_FAILED = -6,
    INVALID_PARAM = -7
};

// ============================================================================
// DATA STRUCTURES
// ============================================================================

struct alignas(64) AESKey {
    uint8_t key[AES_256_KEY_SIZE];
    
    bool is_valid() const {
        for (size_t i = 0; i < AES_256_KEY_SIZE; i++) {
            if (key[i] != 0) return true;
        }
        return false;
    }
    
    void clear() {
        memset(key, 0, AES_256_KEY_SIZE);
    }
};

struct alignas(64) ECDHKeyPair {
    uint8_t private_key[ECDH_KEY_SIZE];
    uint8_t public_key[PUBLIC_KEY_SIZE];
    EC_KEY* ec_key = nullptr;
    
    void clear() {
        memset(private_key, 0, ECDH_KEY_SIZE);
        memset(public_key, 0, PUBLIC_KEY_SIZE);
        if (ec_key) {
            EC_KEY_free(ec_key);
            ec_key = nullptr;
        }
    }
};

struct EncryptedFrame {
    uint8_t* ciphertext = nullptr;
    uint8_t nonce[AES_GCM_IV_SIZE];
    uint8_t tag[AES_GCM_TAG_SIZE];
    size_t ciphertext_size = 0;
    size_t plaintext_size = 0;
    
    // Metadata for tracking
    uint64_t frame_id = 0;
    uint64_t timestamp_us = 0;
    
    EncryptedFrame() {
        memset(nonce, 0, AES_GCM_IV_SIZE);
        memset(tag, 0, AES_GCM_TAG_SIZE);
    }
    
    ~EncryptedFrame() {
        if (ciphertext) {
            delete[] ciphertext;
            ciphertext = nullptr;
        }
    }
    
    size_t total_size() const {
        return ciphertext_size + AES_GCM_IV_SIZE + AES_GCM_TAG_SIZE;
    }
};

struct E2EESession {
    std::string session_id;
    AESKey send_key;
    AESKey recv_key;
    ECDHKeyPair local_ecdh;
    std::vector<uint8_t> remote_public_key;
    bool keys_exchanged = false;
    uint64_t created_at = 0;
    uint64_t last_used_at = 0;
};

// ============================================================================
// ATOMIC STATS
// ============================================================================

struct alignas(64) EncryptionStats {
    std::atomic<uint64_t> frames_encrypted{0};
    std::atomic<uint64_t> frames_decrypted{0};
    std::atomic<uint64_t> encryption_failures{0};
    std::atomic<uint64_t> decryption_failures{0};
    std::atomic<uint64_t> total_bytes_encrypted{0};
    std::atomic<uint64_t> total_bytes_decrypted{0};
    std::atomic<uint64_t> avg_encryption_time_us{0};
    std::atomic<uint64_t> max_encryption_time_us{0};
    std::atomic<uint64_t> avg_decryption_time_us{0};
    std::atomic<uint64_t> max_decryption_time_us{0};
};

// ============================================================================
// AES-256-GCM CRYPTO ENGINE
// ============================================================================

class AESGCMEngine {
public:
    AESGCMEngine();
    ~AESGCMEngine();
    
    // Generate random key
    static bool generate_key(AESKey& key);
    
    // Generate random IV
    static bool generate_iv(uint8_t* iv, size_t size = AES_GCM_IV_SIZE);
    
    // Encrypt single buffer (in-place optional, preferred zero-copy)
    CryptoResult encrypt(
        const uint8_t* plaintext,
        size_t plaintext_len,
        const AESKey& key,
        const uint8_t* iv,
        uint8_t* ciphertext_out,
        uint8_t* tag_out
    );
    
    // Decrypt single buffer
    CryptoResult decrypt(
        const uint8_t* ciphertext,
        size_t ciphertext_len,
        const AESKey& key,
        const uint8_t* iv,
        const uint8_t* tag,
        uint8_t* plaintext_out
    );
    
    // Optimized: Encrypt frame into pre-allocated buffer
    CryptoResult encrypt_frame(
        const uint8_t* plaintext,
        size_t size,
        const AESKey& key,
        EncryptedFrame& output
    );
    
    // Optimized: Decrypt frame
    CryptoResult decrypt_frame(
        const EncryptedFrame& encrypted,
        const AESKey& key,
        uint8_t* plaintext_out,
        size_t& plaintext_out_size
    );

private:
    EVP_CIPHER_CTX* encrypt_ctx = nullptr;
    EVP_CIPHER_CTX* decrypt_ctx = nullptr;
    bool initialized = false;
};

// ============================================================================
// ECDH KEY EXCHANGE
// ============================================================================

class ECDHKeyExchange {
public:
    ECDHKeyExchange();
    ~ECDHKeyExchange();
    
    // Generate key pair
    bool generate_keypair(ECDHKeyPair& keypair);
    
    // Compute shared secret
    bool compute_shared_secret(
        const ECDHKeyPair& local_key,
        const uint8_t* remote_public_key,
        size_t remote_key_size,
        AESKey& shared_key
    );
    
    // Derive session keys from shared secret (HKDF-like)
    static bool derive_session_key(
        const uint8_t* shared_secret,
        size_t secret_size,
        const std::string& session_id,
        AESKey& send_key,
        AESKey& recv_key
    );

private:
    EC_GROUP* curve = nullptr;
    bool initialized = false;
};

// ============================================================================
// E2EE SESSION MANAGER
// ============================================================================

class E2EESessionManager {
public:
    E2EESessionManager();
    ~E2EESessionManager();
    
    // Create new E2EE session
    std::string create_session(const std::string& session_id);
    
    // Get session by ID
    std::shared_ptr<E2EESession> get_session(const std::string& session_id);
    
    // Remove session
    void remove_session(const std::string& session_id);
    
    // Generate public key for session
    std::vector<uint8_t> get_public_key(const std::string& session_id);
    
    // Process remote public key and derive shared keys
    bool complete_key_exchange(
        const std::string& session_id,
        const std::vector<uint8_t>& remote_public_key
    );
    
    // Get stats
    EncryptionStats get_stats() const;
    void reset_stats();

private:
    std::vector<std::shared_ptr<E2EESession>> sessions;
    ECDHKeyExchange ecdh;
    AESGCMEngine aes;
    EncryptionStats stats;
    std::atomic<uint64_t> session_counter{0};
    
    std::mutex session_mutex;
};

// ============================================================================
// REAL-TIME ENCRYPTED PIPELINE
// ============================================================================

class E2EEPipeline {
public:
    E2EEPipeline();
    ~E2EEPipeline();
    
    bool initialize(const std::string& session_id, std::shared_ptr<E2EESession> session);
    
    // Encrypt outgoing frame
    CryptoResult encrypt_outgoing(
        const uint8_t* plaintext,
        size_t size,
        EncryptedFrame& output
    );
    
    // Decrypt incoming frame  
    CryptoResult decrypt_incoming(
        const EncryptedFrame& encrypted,
        uint8_t* plaintext_out,
        size_t& plaintext_out_size
    );
    
    EncryptionStats get_stats() const;

private:
    std::shared_ptr<E2EESession> session;
    AESGCMEngine aes;
    EncryptionStats stats;
    std::atomic<bool> initialized{false};
};

// ============================================================================
// FAST ENCRYPTION HELPERS (SIMD-READY)
// ============================================================================

namespace helpers {

// Generate cryptographically secure random bytes
inline bool secure_random(uint8_t* buffer, size_t size) {
    return RAND_bytes(buffer, size) == 1;
}

// Constant-time comparison (prevent timing attacks)
inline bool constant_time_compare(const uint8_t* a, const uint8_t* b, size_t size) {
    uint8_t diff = 0;
    for (size_t i = 0; i < size; i++) {
        diff |= a[i] ^ b[i];
    }
    return diff == 0;
}

// Fast XOR (for potential SIMD optimization)
inline void fast_xor(uint8_t* dest, const uint8_t* src, size_t size) {
    for (size_t i = 0; i < size; i++) {
        dest[i] ^= src[i];
    }
}

} // namespace helpers

// ============================================================================
// IMPLEMENTATION
// ============================================================================

inline AESGCMEngine::AESGCMEngine() {
    encrypt_ctx = EVP_CIPHER_CTX_new();
    decrypt_ctx = EVP_CIPHER_CTX_new();
    initialized = (encrypt_ctx && decrypt_ctx);
    
    if (initialized) {
        EVP_CIPHER_CTX_init(encrypt_ctx);
        EVP_CIPHER_CTX_init(decrypt_ctx);
    }
}

inline AESGCMEngine::~AESGCMEngine() {
    if (encrypt_ctx) {
        EVP_CIPHER_CTX_free(encrypt_ctx);
    }
    if (decrypt_ctx) {
        EVP_CIPHER_CTX_free(decrypt_ctx);
    }
}

inline bool AESGCMEngine::generate_key(AESKey& key) {
    return helpers::secure_random(key.key, AES_256_KEY_SIZE);
}

inline bool AESGCMEngine::generate_iv(uint8_t* iv, size_t size) {
    return helpers::secure_random(iv, size);
}

inline CryptoResult AESGCMEngine::encrypt(
    const uint8_t* plaintext,
    size_t plaintext_len,
    const AESKey& key,
    const uint8_t* iv,
    uint8_t* ciphertext_out,
    uint8_t* tag_out
) {
    if (!plaintext || !key.is_valid() || !iv || !ciphertext_out || !tag_out) {
        return CryptoResult::INVALID_PARAM;
    }
    
    if (!initialized) {
        return CryptoResult::ENCRYPTION_FAILED;
    }
    
    int len = 0;
    int ciphertext_len = 0;
    
    EVP_EncryptInit_ex(encrypt_ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr);
    EVP_CIPHER_CTX_set_padding(encrypt_ctx, 0);
    EVP_EncryptInit_ex(encrypt_ctx, nullptr, key.key, iv, nullptr);
    
    if (EVP_EncryptUpdate(encrypt_ctx, ciphertext_out, &len, plaintext, plaintext_len) != 1) {
        return CryptoResult::ENCRYPTION_FAILED;
    }
    ciphertext_len = len;
    
    if (EVP_EncryptFinal_ex(encrypt_ctx, ciphertext_out + len, &len) != 1) {
        return CryptoResult::ENCRYPTION_FAILED;
    }
    ciphertext_len += len;
    
    // Get tag
    if (EVP_CIPHER_CTX_ctrl(encrypt_ctx, EVP_CTRL_GCM_GET_TAG, AES_GCM_TAG_SIZE, tag_out) != 1) {
        return CryptoResult::ENCRYPTION_FAILED;
    }
    
    return CryptoResult::SUCCESS;
}

inline CryptoResult AESGCMEngine::decrypt(
    const uint8_t* ciphertext,
    size_t ciphertext_len,
    const AESKey& key,
    const uint8_t* iv,
    const uint8_t* tag,
    uint8_t* plaintext_out
) {
    if (!ciphertext || !key.is_valid() || !iv || !tag || !plaintext_out) {
        return CryptoResult::INVALID_PARAM;
    }
    
    if (!initialized) {
        return CryptoResult::DECRYPTION_FAILED;
    }
    
    int len = 0;
    int plaintext_len = 0;
    
    EVP_DecryptInit_ex(decrypt_ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr);
    EVP_CIPHER_CTX_set_padding(decrypt_ctx, 0);
    EVP_DecryptInit_ex(decrypt_ctx, nullptr, key.key, iv, nullptr);
    
    // Set expected tag
    if (EVP_CIPHER_CTX_ctrl(decrypt_ctx, EVP_CTRL_GCM_SET_TAG, AES_GCM_TAG_SIZE, (void*)tag) != 1) {
        return CryptoResult::DECRYPTION_FAILED;
    }
    
    if (EVP_DecryptUpdate(decrypt_ctx, plaintext_out, &len, ciphertext, ciphertext_len) != 1) {
        return CryptoResult::DECRYPTION_FAILED;
    }
    plaintext_len = len;
    
    if (EVP_DecryptFinal_ex(decrypt_ctx, plaintext_out + len, &len) != 1) {
        return CryptoResult::DECRYPTION_FAILED;
    }
    plaintext_len += len;
    
    return CryptoResult::SUCCESS;
}

inline CryptoResult AESGCMEngine::encrypt_frame(
    const uint8_t* plaintext,
    size_t size,
    const AESKey& key,
    EncryptedFrame& output
) {
    auto start = std::chrono::high_resolution_clock::now();
    
    // Generate fresh nonce for each frame
    generate_iv(output.nonce);
    
    // Allocate output buffer (pre-allocated for zero-copy)
    if (!output.ciphertext) {
        output.ciphertext = new uint8_t[size + ENCRYPTION_OVERHEAD];
    }
    output.ciphertext_size = size;
    output.plaintext_size = size;
    
    // Encrypt
    CryptoResult result = encrypt(
        plaintext,
        size,
        key,
        output.nonce,
        output.ciphertext,
        output.tag
    );
    
    auto end = std::chrono::high_resolution_clock::now();
    auto latency = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    
    return result;
}

inline CryptoResult AESGCMEngine::decrypt_frame(
    const EncryptedFrame& encrypted,
    const AESKey& key,
    uint8_t* plaintext_out,
    size_t& plaintext_out_size
) {
    auto start = std::chrono::high_resolution_clock::now();
    
    CryptoResult result = decrypt(
        encrypted.ciphertext,
        encrypted.ciphertext_size,
        key,
        encrypted.nonce,
        encrypted.tag,
        plaintext_out
    );
    
    if (result == CryptoResult::SUCCESS) {
        plaintext_out_size = encrypted.ciphertext_size - AES_GCM_TAG_SIZE;
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto latency = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    
    return result;
}

// ============================================================================
// ECDH IMPLEMENTATION
// ============================================================================

inline ECDHKeyExchange::ECDHKeyExchange() {
    curve = EC_GROUP_new_by_curve_name(NID_X9_62_prime256v1);
    initialized = (curve != nullptr);
}

inline ECDHKeyExchange::~ECDHKeyExchange() {
    if (curve) {
        EC_GROUP_free(curve);
    }
}

inline bool ECDHKeyExchange::generate_keypair(ECDHKeyPair& keypair) {
    if (!initialized) return false;
    
    keypair.ec_key = EC_KEY_new_by_curve_name(NID_X9_62_prime256v1);
    if (!keypair.ec_key) return false;
    
    EC_KEY_generate_key(keypair.ec_key);
    
    const EC_POINT* pub_key = EC_KEY_get0_public_key(keypair.ec_key);
    const BIGNUM* priv_key = EC_KEY_get0_private_key(keypair.ec_key);
    
    // Extract public key (uncompressed format)
    size_t key_len = EC_POINT_point2oct(curve, pub_key, 
                                         POINT_CONVERSION_UNCOMPRESSED,
                                         keypair.public_key, PUBLIC_KEY_SIZE, nullptr);
    if (key_len != PUBLIC_KEY_SIZE) return false;
    
    // Extract private key
    BN_bn2binpad(priv_key, keypair.private_key, ECDH_KEY_SIZE);
    
    return true;
}

inline bool ECDHKeyExchange::compute_shared_secret(
    const ECDHKeyPair& local_key,
    const uint8_t* remote_public_key,
    size_t remote_key_size,
    AESKey& shared_key
) {
    if (!local_key.ec_key || !remote_public_key) return false;
    
    EC_POINT* remote_point = EC_POINT_new(curve);
    EC_POINT_oct2point(curve, remote_point, remote_public_key, remote_key_size, nullptr);
    
    // Compute shared secret
    size_t secret_len = ECDH_size(local_key.ec_key);
    uint8_t secret[ECDH_KEY_SIZE];
    
    ECDH_compute_key(secret, secret_len, remote_point, local_key.ec_key, nullptr);
    
    // Derive AES key from shared secret
    uint8_t hash[SHA256_DIGEST_LENGTH];
    SHA256(secret, secret_len, hash);
    
    memcpy(shared_key.key, hash, AES_256_KEY_SIZE);
    
    EC_POINT_free(remote_point);
    return true;
}

inline bool ECDHKeyExchange::derive_session_key(
    const uint8_t* shared_secret,
    size_t secret_size,
    const std::string& session_id,
    AESKey& send_key,
    AESKey& recv_key
) {
    // HKDF-like derivation using HMAC-SHA256
    uint8_t send_info[] = "DI_E2EE_SEND_KEY";
    uint8_t recv_info[] = "DI_E2EE_RECV_KEY";
    
    uint8_t send_key_material[SHA256_DIGEST_LENGTH];
    uint8_t recv_key_material[SHA256_DIGEST_LENGTH];
    
    HMAC(EVP_sha256(), shared_secret, secret_size, send_info, sizeof(send_info) - 1, send_key_material, nullptr);
    HMAC(EVP_sha256(), shared_secret, secret_size, recv_info, sizeof(recv_info) - 1, recv_key_material, nullptr);
    
    memcpy(send_key.key, send_key_material, AES_256_KEY_SIZE);
    memcpy(recv_key.key, recv_key_material, AES_256_KEY_SIZE);
    
    return true;
}

// ============================================================================
// SESSION MANAGER IMPLEMENTATION
// ============================================================================

inline E2EESessionManager::E2EESessionManager() {}

inline E2EESessionManager::~E2EESessionManager() {
    sessions.clear();
}

inline std::string E2EESessionManager::create_session(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(session_mutex);
    
    auto session = std::make_shared<E2EESession>();
    session->session_id = session_id;
    session->created_at = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    
    // Generate ECDH key pair for this session
    ecdh.generate_keypair(session->local_ecdh);
    
    sessions.push_back(session);
    
    return session_id;
}

inline std::shared_ptr<E2EESession> E2EESessionManager::get_session(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(session_mutex);
    
    for (auto& s : sessions) {
        if (s->session_id == session_id) {
            return s;
        }
    }
    return nullptr;
}

inline void E2EESessionManager::remove_session(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(session_mutex);
    
    sessions.erase(
        std::remove_if(sessions.begin(), sessions.end(),
            [&session_id](const std::shared_ptr<E2EESession>& s) {
                return s->session_id == session_id;
            }),
        sessions.end()
    );
}

inline std::vector<uint8_t> E2EESessionManager::get_public_key(const std::string& session_id) {
    auto session = get_session(session_id);
    if (!session) return {};
    
    std::vector<uint8_t> pub_key(session->local_ecdh.public_key, 
                                 session->local_ecdh.public_key + PUBLIC_KEY_SIZE);
    return pub_key;
}

inline bool E2EESessionManager::complete_key_exchange(
    const std::string& session_id,
    const std::vector<uint8_t>& remote_public_key
) {
    auto session = get_session(session_id);
    if (!session || remote_public_key.empty()) return false;
    
    AESKey shared_key;
    if (!ecdh.compute_shared_secret(session->local_ecdh, 
                                     remote_public_key.data(), 
                                     remote_public_key.size(), 
                                     shared_key)) {
        return false;
    }
    
    // Derive session keys
    ecdh.derive_session_key(shared_key.key, ECDH_KEY_SIZE, session_id, 
                           session->send_key, session->recv_key);
    
    session->remote_public_key = remote_public_key;
    session->keys_exchanged = true;
    
    return true;
}

inline EncryptionStats E2EESessionManager::get_stats() const {
    return stats;
}

inline void E2EESessionManager::reset_stats() {
    stats = EncryptionStats();
}

// ============================================================================
// PIPELINE IMPLEMENTATION
// ============================================================================

inline E2EEPipeline::E2EEPipeline() {}

inline E2EEPipeline::~E2EEPipeline() {}

inline bool E2EEPipeline::initialize(const std::string& session_id, 
                                     std::shared_ptr<E2EESession> sess) {
    session = sess;
    initialized.store(session && session->keys_exchanged);
    return initialized.load();
}

inline CryptoResult E2EEPipeline::encrypt_outgoing(
    const uint8_t* plaintext,
    size_t size,
    EncryptedFrame& output
) {
    if (!initialized.load() || !session) {
        return CryptoResult::INVALID_KEY;
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    CryptoResult result = aes.encrypt_frame(plaintext, size, session->send_key, output);
    
    auto end = std::chrono::high_resolution_clock::now();
    auto latency = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    
    if (result == CryptoResult::SUCCESS) {
        stats.frames_encrypted.increment();
        stats.total_bytes_encrypted.fetch_add(size);
        
        auto current_max = stats.max_encryption_time_us.load();
        if (latency > current_max) {
            stats.max_encryption_time_us.store(latency);
        }
        stats.avg_encryption_time_us.store(
            (stats.avg_encryption_time_us.load() + latency) / 2
        );
    } else {
        stats.encryption_failures.increment();
    }
    
    return result;
}

inline CryptoResult E2EEPipeline::decrypt_incoming(
    const EncryptedFrame& encrypted,
    uint8_t* plaintext_out,
    size_t& plaintext_out_size
) {
    if (!initialized.load() || !session) {
        return CryptoResult::INVALID_KEY;
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    CryptoResult result = aes.decrypt_frame(encrypted, session->recv_key, 
                                           plaintext_out, plaintext_out_size);
    
    auto end = std::chrono::high_resolution_clock::now();
    auto latency = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    
    if (result == CryptoResult::SUCCESS) {
        stats.frames_decrypted.increment();
        stats.total_bytes_decrypted.fetch_add(plaintext_out_size);
        
        auto current_max = stats.max_decryption_time_us.load();
        if (latency > current_max) {
            stats.max_decryption_time_us.store(latency);
        }
        stats.avg_decryption_time_us.store(
            (stats.avg_decryption_time_us.load() + latency) / 2
        );
    } else {
        stats.decryption_failures.increment();
    }
    
    return result;
}

inline EncryptionStats E2EEPipeline::get_stats() const {
    return stats;
}

} // namespace crypto
} // namespace di

#endif // DI_E2EE_ENGINE_H