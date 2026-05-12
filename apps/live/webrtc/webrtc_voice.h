#ifndef WEBRTC_VOICE_H
#define WEBRTC_VOICE_H

#include <string>
#include <vector>
#include <memory>
#include <functional>

namespace di {

struct AudioChunk {
    std::vector<uint8_t> data;
    int sample_rate;
    int channels;
    int bits_per_sample;
};

struct VoiceSession {
    int user_id;
    std::string session_id;
    bool is_active;
    std::string remote_peer_id;
};

class WebRTCVoiceEngine {
public:
    WebRTCVoiceEngine();
    ~WebRTCVoiceEngine();

    bool initialize();
    
    std::string create_session(int user_id);
    bool join_session(const std::string& session_id, const std::string& peer_id);
    bool leave_session(const std::string& session_id);
    
    bool send_audio(const std::string& session_id, const AudioChunk& audio);
    bool receive_audio(const std::string& session_id, AudioChunk& output);
    
    std::string get_stats(const std::string& session_id);
    
private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

class STTEngine {
public:
    STTEngine();
    bool initialize();
    std::string transcribe(const AudioChunk& audio);
};

class TTSEngine {
public:
    TTSEngine();
    bool initialize();
    AudioChunk synthesize(const std::string& text, const std::string& voice = "Aoede");
};

}

#endif