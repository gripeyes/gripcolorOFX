#pragma once
// Diagnostic bookkeeping only: never changes render outcomes or host declarations.
#include "ofxImageEffect.h"
#include "ofxGPURender.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <thread>
#include <chrono>
#include <exception>
#include <limits>
#include <map>

namespace rendition::ofx_trace {
constexpr size_t historyCapacity = 128;
struct Event {
    uint64_t sequence = 0, renderId = 0;
    int64_t microseconds = 0;
    const void *instance = nullptr, *clip = nullptr;
    size_t thread = 0;
    int effect = -1;
    unsigned active = 0;
    double time = 0;
    OfxRectI window{};
    double scale[2]{std::numeric_limits<double>::quiet_NaN(), std::numeric_limits<double>::quiet_NaN()};
    int interactive = -1, gpu = -1, cuda = -1, openCL = -1, abortBefore = -1, abortAfter = -1, fetchStatus = -1;
    // Window, scale, field, interactive, Metal, CUDA and OpenCL property read statuses.
    std::array<int, 7> propertyStatus{{-1,-1,-1,-1,-1,-1,-1}};
    char field[64] = "unknown", stage[32] = "none", role[32] = "none";
};
struct History {
    std::array<Event, historyCapacity> events{};
    size_t size = 0;
};
struct State {
    std::mutex mutex;
    std::array<Event, historyCapacity> events{};
    size_t next = 0, size = 0;
    uint64_t nextRender = 0, nextEvent = 0;
    std::map<const void *, unsigned> active;
};
inline State state;
inline thread_local Event *current = nullptr;
inline bool enabled() {
    const char *value = std::getenv("RENDITION_SUITE_TRACE");
    return value && std::strcmp(value, "1") == 0;
}
inline void recordLocked(Event event) {
    event.sequence = ++state.nextEvent;
    event.microseconds = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    event.thread = std::hash<std::thread::id>{}(std::this_thread::get_id());
    const auto found = state.active.find(event.instance);
    event.active = found == state.active.end() ? 0 : found->second;
    state.events[state.next] = event;
    state.next = (state.next + 1) % historyCapacity;
    state.size = std::min(state.size + 1, historyCapacity);
}
inline void record(const Event &event) noexcept {
    try { std::lock_guard<std::mutex> lock(state.mutex); recordLocked(event); } catch (...) {}
}
inline History snapshot() {
    History result;
    std::lock_guard<std::mutex> lock(state.mutex);
    result.size = state.size;
    const auto first = (state.next + historyCapacity - state.size) % historyCapacity;
    for (size_t n = 0; n < state.size; ++n)
        result.events[n] = state.events[(first + n) % historyCapacity];
    return result;
}
inline void dump() noexcept {
    if (!enabled()) return;
    try {
        // Copy while locked; formatting/I/O never holds the bookkeeping mutex.
        const auto history = snapshot();
        for (size_t n = 0; n < history.size; ++n) {
            const auto &e = history.events[n];
            std::fprintf(stderr,
                "Rendition render history: seq=%llu render_id=%llu us=%lld "
                "action=OfxImageEffectActionRender stage=%s effect=%d instance=%p "
                "thread=%zu active_renders=%u time=%.17g window=%d,%d,%d,%d "
                "scale=%.17g,%.17g field=%s interactive=%d gpu_metal=%d gpu_cuda=%d gpu_opencl=%d "
                "property_status=%d,%d,%d,%d,%d,%d,%d subject=%s clip=%p "
                "abort_before_fetch=%d fetch_status=%d abort_after_fetch=%d\n",
                (unsigned long long)e.sequence, (unsigned long long)e.renderId,
                (long long)e.microseconds, e.stage, e.effect, e.instance, e.thread,
                e.active, e.time, e.window.x1, e.window.y1, e.window.x2, e.window.y2,
                e.scale[0], e.scale[1], e.field, e.interactive, e.gpu, e.cuda, e.openCL,
                e.propertyStatus[0], e.propertyStatus[1], e.propertyStatus[2],
                e.propertyStatus[3], e.propertyStatus[4], e.propertyStatus[5], e.propertyStatus[6], e.role, e.clip,
                e.abortBefore, e.fetchStatus, e.abortAfter);
        }
    } catch (...) {} // Diagnostics must not replace the original failure.
}
class RenderScope {
    Event event;
    Event *previous = current;
    int exceptions = std::uncaught_exceptions();
    bool registered = false;
public:
    RenderScope(const void *instance, int effect, double time,
                OfxPropertySetHandle args, const OfxPropertySuiteV1 *properties) noexcept {
        if (!enabled()) return;
        event.instance = instance; event.effect = effect; event.time = time;
        try {
            {
                std::lock_guard<std::mutex> lock(state.mutex);
                ++state.active[instance];
                registered = true;
                event.renderId = ++state.nextRender;
            }
            current = &event;
            if (properties) {
                if (properties->propGetIntN)
                    event.propertyStatus[0] = properties->propGetIntN(args, kOfxImageEffectPropRenderWindow, 4, &event.window.x1);
                if (properties->propGetDoubleN)
                    event.propertyStatus[1] = properties->propGetDoubleN(args, kOfxImageEffectPropRenderScale, 2, event.scale);
                char *field = nullptr;
                if (properties->propGetString) {
                    event.propertyStatus[2] = properties->propGetString(args, kOfxImageEffectPropFieldToRender, 0, &field);
                    if (event.propertyStatus[2] == kOfxStatOK && field)
                        std::snprintf(event.field, sizeof(event.field), "%s", field);
                }
                if (properties->propGetInt) {
                    int value = -1;
                    event.propertyStatus[3] = properties->propGetInt(args, kOfxImageEffectPropInteractiveRenderStatus, 0, &value);
                    if (event.propertyStatus[3] == kOfxStatOK) event.interactive = value;
                    value = -1;
                    event.propertyStatus[4] = properties->propGetInt(args, kOfxImageEffectPropMetalEnabled, 0, &value);
                    if (event.propertyStatus[4] == kOfxStatOK) event.gpu = value;
                    value = -1;
                    event.propertyStatus[5] = properties->propGetInt(args, kOfxImageEffectPropCudaEnabled, 0, &value);
                    if (event.propertyStatus[5] == kOfxStatOK) event.cuda = value;
                    value = -1;
                    event.propertyStatus[6] = properties->propGetInt(args, kOfxImageEffectPropOpenCLEnabled, 0, &value);
                    if (event.propertyStatus[6] == kOfxStatOK) event.openCL = value;
                }
            }
            std::snprintf(event.stage, sizeof(event.stage), "render-entry");
            record(event);
        } catch (...) {} // Optional instrumentation does not fail the effect.
    }
    ~RenderScope() noexcept {
        if (!registered) return;
        const bool cancelled = std::strcmp(event.stage, "render-cancelled") == 0;
        std::snprintf(event.stage, sizeof(event.stage), "%s", cancelled ? "render-exit-cancelled" :
                      std::uncaught_exceptions() > exceptions ? "render-exit-error" : "render-exit");
        record(event);
        current = previous;
        try {
            std::lock_guard<std::mutex> lock(state.mutex);
            auto found = state.active.find(event.instance);
            if (found != state.active.end() && --found->second == 0) state.active.erase(found);
        } catch (...) {} // Trace cleanup must not replace a render exception.
    }
};
// Called only with tracing enabled inside Render. No recovery or early return here.
inline Event acquisitionBefore(OfxImageClipHandle clip, const char *role,
                               const OfxImageEffectSuiteV1 *effects, int sampledAbort = -1) {
    Event e = *current;
    e.clip = clip;
    std::snprintf(e.role, sizeof(e.role), "%s", role);
    std::snprintf(e.stage, sizeof(e.stage), "acquire-before");
    e.abortBefore = sampledAbort;
    if (sampledAbort < 0 && effects->abort)
        e.abortBefore = effects->abort(const_cast<OfxImageEffectHandle>(
            static_cast<const OfxImageEffectStruct *>(e.instance)));
    record(e);
    return e;
}
inline void acquisitionAfter(Event e, OfxStatus status, const OfxImageEffectSuiteV1 *effects, int sampledAbort = -1) {
    e.fetchStatus = status;
    std::snprintf(e.stage, sizeof(e.stage), "acquire-result");
    e.abortAfter = sampledAbort;
    if (sampledAbort < 0 && status != kOfxStatOK && effects->abort)
        e.abortAfter = effects->abort(const_cast<OfxImageEffectHandle>(
            static_cast<const OfxImageEffectStruct *>(e.instance)));
    record(e);
}
} // namespace rendition::ofx_trace
