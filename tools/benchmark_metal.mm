#include "rendition/kernel_bridge.hpp"
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <chrono>
#include <fstream>
#include <iostream>
using namespace rendition;
int main(int argc, char **argv) {
    @autoreleasepool {
        if (argc != 3)
            return 2;
        id<MTLDevice> dev = MTLCreateSystemDefaultDevice();
        if (!dev)
            return 2;
        NSError *err = nil;
        id<MTLLibrary> lib =
            [dev newLibraryWithURL:[NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[1]]]
                             error:&err];
        if (!lib) {
            std::cerr << [[err description] UTF8String];
            return 2;
        }
        id<MTLComputePipelineState> pipe =
            [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"renditionPoints"] error:&err];
        if (!pipe)
            return 2;
        id<MTLCommandQueue> queue = [dev newCommandQueue];
        auto &table = spectralTable();
        id<MTLBuffer> tb = [dev newBufferWithBytes:table.data()
                                            length:table.size() * sizeof(float)
                                           options:MTLResourceStorageModeShared];
        auto B = spectralBasis(), inverse = spectralBasis(true);
        struct Case {
            Effect effect;
            Values params;
        };
        std::vector<Case> cases = {{Effect::Scene, {{"exposure", .5}}},
                                   {Effect::Tone, {{"contrast", 1.1}, {"toe", .2}}},
                                   {Effect::Volume, {{"v0_width", 360}, {"v0_hueDelta", 10}}},
                                   {Effect::Density, {{"density", .5}}},
                                   {Effect::Crossover, {{"width", 360}, {"brightHue", 10}}},
                                   {Effect::Crosstalk, {{"rg", .1}}},
                                   {Effect::Strip, {{"separation", .5}}}};
        std::ofstream report(argv[2]);
        report << "{\"device\":\"" << [[dev name] UTF8String]
               << "\",\"method\":\"Offline contiguous RGBA buffers; command GPU time excludes upload, "
                  "allocation, validation, and OFX host overhead. No host FPS claim.\",\"measurements\":[\n";
        bool first = true;
        for (auto size :
             std::vector<std::pair<unsigned, unsigned>>{{1920, 1080}, {3840, 2160}, {7680, 4320}}) {
            unsigned count = size.first * size.second;
            size_t bytes = size_t(count) * 4 * sizeof(float);
            id<MTLBuffer> src = [dev newBufferWithLength:bytes options:MTLResourceStorageModeShared],
                          dst = [dev newBufferWithLength:bytes options:MTLResourceStorageModeShared],
                          status = [dev newBufferWithLength:size_t(count) * sizeof(unsigned)
                                                    options:MTLResourceStorageModeShared];
            if (!src || !dst || !status)
                return 2;
            auto data = static_cast<float *>(src.contents);
            for (unsigned i = 0; i < count; i++) {
                float t = 2.f * (i % size.first) / (size.first - 1);
                data[4 * i] = .01f + .3f * t;
                data[4 * i + 1] = .03f + .4f * t;
                data[4 * i + 2] = .05f + .6f * t;
                data[4 * i + 3] = .4f;
            }
            for (auto test : cases) {
                test.params["interpretation"] = 1;
                Snapshot snapshot(test.effect, test.params);
                auto parameters = snapshot.packed();
                id<MTLCommandBuffer> cmd = [queue commandBuffer];
                id<MTLComputeCommandEncoder> enc = [cmd computeCommandEncoder];
                [enc setComputePipelineState:pipe];
                [enc setBuffer:src offset:0 atIndex:0];
                [enc setBuffer:dst offset:0 atIndex:1];
                [enc setBytes:&parameters length:sizeof(parameters) atIndex:2];
                [enc setBuffer:tb offset:0 atIndex:3];
                [enc setBytes:&B length:sizeof(B) atIndex:4];
                [enc setBytes:&inverse length:sizeof(inverse) atIndex:5];
                [enc setBuffer:status offset:0 atIndex:6];
                [enc setBytes:&count length:sizeof(count) atIndex:7];
                [enc dispatchThreads:MTLSizeMake(count, 1, 1)
                    threadsPerThreadgroup:MTLSizeMake(
                                              std::min<NSUInteger>(256, pipe.maxTotalThreadsPerThreadgroup),
                                              1, 1)];
                [enc endEncoding];
                [cmd commit];
                [cmd waitUntilCompleted];
                if (cmd.status == MTLCommandBufferStatusError)
                    return 1;
                auto flags = static_cast<const unsigned *>(status.contents);
                for (unsigned i = 0; i < count; i++)
                    if (flags[i])
                        return 1;
                double seconds = cmd.GPUEndTime - cmd.GPUStartTime;
                if (seconds <= 0)
                    return 1;
                std::cout << name(test.effect) << " " << size.first << "x" << size.second
                          << " GPU seconds=" << seconds << "\n";
                if (!first)
                    report << ",\n";
                first = false;
                report << "{\"effect\":\"" << name(test.effect) << "\",\"width\":" << size.first
                       << ",\"height\":" << size.second << ",\"gpu_seconds\":" << seconds
                       << ",\"megapixels_per_second\":" << count / seconds / 1e6 << "}";
            }
        }
        report << "\n]}\n";
        return 0;
    }
}
