#ifndef NANO_ENGINE_H
#define NANO_ENGINE_H

#include <atomic>
#include <memory>
#include <vector>
#include <chrono>
#include <functional>
#include <string>

namespace di {
namespace nano {

using Timestamp = std::chrono::high_resolution_clock::time_point;
using Duration = std::chrono::microseconds;

constexpr size_t RING_BUFFER_SIZE = 2048;
constexpr int SAMPLE_RATE = 48000;
constexpr int CHANNELS = 1;
constexpr size_t MAX_LATENCY_US = 50000;

struct AudioFrame {
    uint8_t* data;
    size_t size;
    Timestamp timestamp;
    int sequence;
};

struct VideoFrame {
    uint8_t* data;
    size_t width;
    size_t height;
    size_t size;
    Timestamp timestamp;
};

struct NanoStats {
    uint64_t frames_processed;
    uint64_t bytes_sent;
    uint64_t bytes_received;
    int64_t avg_latency_us;
    int64_t min_latency_us;
    int64_t max_latency_us;
    double packet_loss_percent;
    double jitter_ms;
};

class LockFreeRingBuffer {
private:
    struct Node {
        alignas(64) std::atomic<bool> written{false};
        alignas(64) std::atomic<bool> read{false};
        uint8_t data[4096];
        size_t size = 0;
    };
    
    std::vector<Node> buffer;
    alignas(64) std::atomic<size_t> write_pos{0};
    alignas(64) std::atomic<size_t> read_pos{0};

public:
    LockFreeRingBuffer(size_t size = RING_BUFFER_SIZE) : buffer(size) {}
    
    bool write(const uint8_t* data, size_t size) {
        size_t write_idx = write_pos.load(std::memory_order_relaxed);
        Node& node = buffer[write_idx % buffer.size()];
        
        if (node.written.load(std::memory_order_acquire)) {
            return false;
        }
        
        if (size > sizeof(node.data)) return false;
        memcpy(node.data, data, size);
        node.size = size;
        node.written.store(true, std::memory_order_release);
        write_pos.fetch_add(1, std::memory_order_relaxed);
        return true;
    }
    
    bool read(uint8_t* output, size_t& size) {
        size_t read_idx = read_pos.load(std::memory_order_relaxed);
        Node& node = buffer[read_idx % buffer.size()];
        
        if (!node.written.load(std::memory_order_acquire)) {
            return false;
        }
        
        size = node.size;
        memcpy(output, node.data, size);
        node.read.store(true, std::memory_order_release);
        node.written.store(false, std::memory_order_release);
        read_pos.fetch_add(1, std::memory_order_relaxed);
        return true;
    }
};

class AtomicCounter {
private:
    alignas(64) std::atomic<uint64_t> value{0};
    
public:
    void increment() { value.fetch_add(1, std::memory_order_relaxed); }
    uint64_t get() const { return value.load(std::memory_order_relaxed); }
    void reset() { value.store(0, std::memory_order_relaxed); }
};

class LatencyTracker {
private:
    static constexpr size_t WINDOW_SIZE = 100;
    int64_t latencies[WINDOW_SIZE];
    size_t index = 0;
    size_t count = 0;
    alignas(64) std::mutex mtx;

public:
    void record(int64_t latency_us) {
        std::lock_guard<std::mutex> lock(mtx);
        latencies[index] = latency_us;
        index = (index + 1) % WINDOW_SIZE;
        count = std::min(count + 1, WINDOW_SIZE);
    }
    
    int64_t average() const {
        if (count == 0) return 0;
        int64_t sum = 0;
        for (size_t i = 0; i < count; i++) sum += latencies[i];
        return sum / count;
    }
    
    int64_t min() const {
        if (count == 0) return 0;
        int64_t min_val = INT64_MAX;
        for (size_t i = 0; i < count; i++) min_val = std::min(min_val, latencies[i]);
        return min_val;
    }
    
    int64_t max() const {
        if (count == 0) return 0;
        int64_t max_val = 0;
        for (size_t i = 0; i < count; i++) max_val = std::max(max_val, latencies[i]);
        return max_val;
    }
};

}
}

#endif