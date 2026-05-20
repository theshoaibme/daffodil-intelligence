#include "nano_webrtc_engine.h"
#include <iostream>
#include <chrono>
#include <thread>
#include <atomic>
#include <fstream>

using namespace di::live;

void print_stats(const LatencyStats& stats) {
    printf("\r[FPS: %.1f] [Captured: %lu] [Encoded: %lu] [Sent: %lu] [Avg Latency: %ldms] [Min: %ldms] [Max: %ldms]",
           stats.fps.load(),
           stats.frames_captured.get(),
           stats.frames_encoded.get(),
           stats.packets_sent.get(),
           stats.avg_latency_us.load() / 1000,
           stats.min_latency_us.load() / 1000,
           stats.max_latency_us.load() / 1000);
    fflush(stdout);
}

int main() {
    std::cout << "=============================================================\n";
    std::cout << "  DI REAL-TIME WEBRTC + AI STREAMING ENGINE (C++)\n";
    std::cout << "  Build: Production Grade | Latency Target: <50ms\n";
    std::cout << "=============================================================\n\n";

    // Create engine
    WebRTCEngine engine;

    // Configure pipeline
    PipelineConfig config;
    config.target_fps = 30;
    config.target_bitrate_kbps = 2500;
    config.keyframe_interval_sec = 2;
    config.audio_bitrate_kbps = 128;
    config.enable_gpu_encoding = true;
    config.enable_nvenc = true;
    config.enable_screen_share = true;
    config.ai_frame_interval_ms = 100;

    // Initialize
    std::cout << "[INIT] Initializing WebRTC engine...\n";
    if (!engine.initialize(config)) {
        std::cerr << "Failed to initialize engine\n";
        return 1;
    }

    // Setup callbacks
    engine.set_stats_callback(print_stats);

    // Create session
    std::string session_id = engine.create_session(12345);
    std::cout << "[SESSION] Created: " << session_id << "\n";

    // Start capture
    engine.start_capture(MediaSource::SCREEN_SHARE);
    std::cout << "[CAPTURE] Started screen capture\n";

    // Simulate running for demo
    std::cout << "\n[RUNNING] Processing frames...\n";
    std::cout << "Thread Model:\n";
    std::cout << "  Thread 1: Capture (<100us)\n";
    std::cout << "  Thread 2: Encoding (<2ms)\n";
    std::cout << "  Thread 3: Network (<30ms)\n";
    std::cout << "  Thread 4: AI Processing (<50ms)\n";
    std::cout << "  Thread 5: Stats/UI (<5ms)\n\n";

    // Run for demonstration
    auto start_time = std::chrono::steady_clock::now();
    int iteration = 0;
    
    while (iteration < 100) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        // Update FPS calculation
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start_time).count();
        if (elapsed > 0) {
            LatencyStats stats = engine.get_stats();
            stats.fps.store(stats.frames_captured.get() / (double)elapsed);
        }
        
        iteration++;
    }

    // Cleanup
    engine.stop_capture(MediaSource::SCREEN_SHARE);
    engine.leave_session(session_id);

    std::cout << "\n\n=============================================================\n";
    std::cout << "  FINAL STATISTICS\n";
    std::cout << "=============================================================\n";
    
    LatencyStats final_stats = engine.get_stats();
    std::cout << "Frames captured: " << final_stats.frames_captured.get() << "\n";
    std::cout << "Frames encoded:  " << final_stats.frames_encoded.get() << "\n";
    std::cout << "Packets sent:     " << final_stats.packets_sent.get() << "\n";
    std::cout << "Min latency:      " << final_stats.min_latency_us.load() << " us\n";
    std::cout << "Max latency:      " << final_stats.max_latency_us.load() << " us\n";
    std::cout << "Avg latency:      " << final_stats.avg_latency_us.load() << " us\n";
    
    std::cout << "\n[SUCCESS] WebRTC Engine shutdown complete\n";
    
    return 0;
}