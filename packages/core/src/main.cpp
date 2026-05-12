#include <iostream>
#include <rtc/rtc.hpp>

int main() {
    std::cout << "Initializing WebRTC (libdatachannel)..." << std::endl;
    
    // Initialize the library logger
    rtc::InitLogger(rtc::LogLevel::Info);
    
    std::cout << "WebRTC initialized successfully." << std::endl;
    return 0;
}
