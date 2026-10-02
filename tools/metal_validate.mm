#include "rendition/kernel_bridge.hpp"
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
using namespace rendition;
int main(int argc, char **argv) {
    @autoreleasepool {
        if (argc < 3) {
            std::cerr << "Usage: metal_validate metallib report.json\n";
            return 2;
        }
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        if (!device) {
            std::cerr << "No Metal device\n";
            return 2;
        }
        NSError *error = nil;
        id<MTLLibrary> library =
            [device newLibraryWithURL:[NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[1]]]
                                error:&error];
        if (!library) {
            std::cerr << [[error description] UTF8String] << "\n";
            return 2;
        }
        id<MTLFunction> function = [library newFunctionWithName:@"renditionPoints"];
        id<MTLComputePipelineState> pipeline = [device newComputePipelineStateWithFunction:function
                                                                                     error:&error];
        if (!pipeline) {
            std::cerr << [[error description] UTF8String] << "\n";
            return 2;
        }
        id<MTLCommandQueue> queue = [device newCommandQueue];
        const auto &table = spectralTable();
        id<MTLBuffer> tb = [device newBufferWithBytes:table.data()
                                               length:table.size() * sizeof(float)
                                              options:MTLResourceStorageModeShared];
        auto B = spectralBasis(), inv = spectralBasis(true);
        struct Case {
            Effect effect;
            Values values;
            std::string name;
        };
        std::vector<Case> cases;
        for (int e = 0; e < 8; e++)
            cases.push_back({Effect(e), {}, "default " + std::string(name(Effect(e)))});
        cases.push_back({Effect::Scene,
                         {{"exposure", 1.1},
                          {"rExposure", .25},
                          {"temperature", 5500},
                          {"tint", .001},
                          {"rPower", 1.05},
                          {"saturation", .9}},
                         "Scene linear"});
        cases.push_back(
            {Effect::Scene, {{"cdlDomain", 1}, {"rPower", 1.04}, {"gOffset", .02}}, "Scene look"});
        for (int d = 1; d <= 5; d++)
            if (d != 4)
                cases.push_back({Effect::Tone,
                                 {{"lookDomain", d},
                                  {"contrast", .9},
                                  {"toe", .3},
                                  {"shoulder", .2},
                                  {"shadowDensity", .1}},
                                 "Tone domain " + std::to_string(d)});
        cases.push_back({Effect::Tone,
                         {{"linked", 1}, {"contrast", 1.1}, {"bContrast", .9}, {"toe", .3}},
                         "Tone per-channel"});
        for (int overlap = 0; overlap < 4; overlap++)
            cases.push_back({Effect::Volume,
                             {{"overlap", overlap},
                              {"v0_width", 360},
                              {"v1_width", 360},
                              {"v0_hueDelta", 12},
                              {"v1_hueDelta", -7},
                              {"v0_chroma", 1.1},
                              {"v1_exposure", .25},
                              {"v0_matrixMix", .2},
                              {"v0_m01", .01}},
                             "Volume overlap " + std::to_string(overlap)});
        cases.push_back({Effect::Density, {{"density", .6}}, "Density"});
        cases.push_back(
            {Effect::Density, {{"density", -.4}, {"chromaCoupling", .5}}, "Density negative control"});
        cases.push_back({Effect::Crossover,
                         {{"width", 360}, {"darkHue", -7}, {"brightChroma", .9}, {"midDensity", .1}},
                         "Hue crossover"});
        cases.push_back(
            {Effect::Crossover, {{"mode", 1}, {"darkr", .2}, {"brightb", -.1}}, "Channel crossover"});
        for (int mode = 0; mode < 4; mode++)
            cases.push_back({Effect::Crosstalk,
                             {{"mode", mode}, {"rg", .2}, {"br", -.1}, {"rowSum", .8}},
                             "Crosstalk mode " + std::to_string(mode)});
        cases.push_back({Effect::Crosstalk, {{"domain", 1}, {"rg", .1}}, "Crosstalk look"});
        for (int mode = 0; mode < 3; mode++)
            cases.push_back(
                {Effect::Strip,
                 {{"mode", mode}, {"separation", .6}, {"density", .2}, {"redAnchor", .5}, {"m01", .02}},
                 "Strip mode " + std::to_string(mode)});
        cases.push_back({Effect::Inspector, {{"mode", 9}}, "Inspector gamut"});
        cases.push_back({Effect::Inspector, {{"mode", 10}}, "Inspector nonfinite"});
        std::mt19937 rng(20261002);
        std::uniform_real_distribution<float> sample(-1, 1), exposure(-10, 10);
        unsigned count = 8192;
        std::vector<std::array<float, 4>> input(count);
        for (auto &rgba : input) {
            float scale = std::exp2(exposure(rng));
            rgba = {sample(rng) * scale, sample(rng) * scale, sample(rng) * scale, .4f};
        }
        input[0] = {.18f, .18f, .18f, .37f};
        input[1] = {0, 0, 0, 0};
        input[2] = {-.1f, .2f, 4, .4f};
        input[3] = {std::numeric_limits<float>::quiet_NaN(), 1, 2, .4f};
        id<MTLBuffer> src = [device newBufferWithBytes:input.data()
                                                length:input.size() * sizeof(input[0])
                                               options:MTLResourceStorageModeShared],
                      dst = [device newBufferWithLength:input.size() * sizeof(input[0])
                                                options:MTLResourceStorageModeShared],
                      flags = [device newBufferWithLength:count * sizeof(unsigned)
                                                  options:MTLResourceStorageModeShared];
        std::ofstream report(argv[2]);
        report << "{\n  \"device\": \"" << [[device name] UTF8String]
               << "\",\n  \"samples_per_case\": " << count << ",\n  \"cases\": [\n";
        bool failed = false;
        int caseIndex = 0;
        for (auto test : cases) {
            test.values["interpretation"] = 1;
            test.values["alphaMode"] = caseIndex % 2;
            Snapshot snapshot(test.effect, test.values);
            auto p = snapshot.packed();
            id<MTLCommandBuffer> command = [queue commandBuffer];
            id<MTLComputeCommandEncoder> encoder = [command computeCommandEncoder];
            [encoder setComputePipelineState:pipeline];
            [encoder setBuffer:src offset:0 atIndex:0];
            [encoder setBuffer:dst offset:0 atIndex:1];
            [encoder setBytes:&p length:sizeof(p) atIndex:2];
            [encoder setBuffer:tb offset:0 atIndex:3];
            [encoder setBytes:&B length:sizeof(B) atIndex:4];
            [encoder setBytes:&inv length:sizeof(inv) atIndex:5];
            [encoder setBuffer:flags offset:0 atIndex:6];
            [encoder setBytes:&count length:sizeof(count) atIndex:7];
            NSUInteger width = std::min<NSUInteger>(pipeline.maxTotalThreadsPerThreadgroup, 256);
            [encoder dispatchThreads:MTLSizeMake(count, 1, 1) threadsPerThreadgroup:MTLSizeMake(width, 1, 1)];
            [encoder endEncoding];
            [command commit];
            [command waitUntilCompleted];
            if (command.status == MTLCommandBufferStatusError) {
                std::cerr << [[command.error description] UTF8String] << "\n";
                return 1;
            }
            auto gpu = static_cast<const float *>([dst contents]);
            auto status = static_cast<const unsigned *>([flags contents]);
            double maxRatio = 0, maxAbs = 0;
            unsigned errors = 0, matchedFailures = 0, strictFailures = 0;
            double maxVectorRelative = 0;
            for (unsigned i = 0; i < count; i++) {
                std::array<float, 4> cpu;
                try {
                    cpu = snapshot.pixel(input[i]);
                } catch (const std::exception &) {
                    if (status[i]) {
                        matchedFailures++;
                        continue;
                    }
                    errors++;
                    continue;
                }
                if (status[i]) {
                    errors++;
                    continue;
                }
                for (int j = 0; j < 4; j++) {
                    float g = gpu[4 * i + j], r = cpu[j];
                    if (std::isnan(g) && std::isnan(r))
                        continue;
                    if (g == r)
                        continue;
                    double diff = std::abs(double(g) - r), strictRatio = diff / (5e-6 + 5e-5 * std::abs(r));
                    double vectorScale = std::max({std::abs(cpu[0]), std::abs(cpu[1]), std::abs(cpu[2])});
                    double allowance = j < 3 && std::abs(r) < .02 * vectorScale ? 1e-6 * vectorScale : 0;
                    double ratio = diff / (5e-6 + 5e-5 * std::abs(r) + allowance);
                    if (strictRatio > 1)
                        strictFailures++;
                    maxVectorRelative = std::max(maxVectorRelative, diff / std::max(vectorScale, 1e-12));
                    maxRatio = std::max(maxRatio, ratio);
                    maxAbs = std::max(maxAbs, diff);
                    if (ratio > 1 || !std::isfinite(g)) {
                        if (errors < 3)
                            std::cerr << "Mismatch " << test.name << " sample " << i << " channel " << j
                                      << " CPU=" << r << " GPU=" << g << " input=" << input[i][0] << ","
                                      << input[i][1] << "," << input[i][2] << " ratio=" << ratio << "\n";
                        errors++;
                    }
                }
            }
            std::cout << test.name << ": errors=" << errors << " maxRatio=" << maxRatio << "\n";
            failed |= errors != 0;
            if (caseIndex++)
                report << ",\n";
            report << "    {\"name\": \"" << test.name << "\", \"errors\": " << errors
                   << ", \"matched_invalid_inputs\": " << matchedFailures
                   << ", \"max_tolerance_ratio\": " << maxRatio << ", \"max_absolute_error\": " << maxAbs
                   << ", \"strict_component_failures\": " << strictFailures
                   << ", \"max_vector_relative_error\": " << maxVectorRelative << "}";
        }
        report << "\n  ],\n  \"passed\": " << (failed ? "false" : "true")
               << ",\n  \"host_enabled\": false,\n  \"host_limitation\": \"OFX asynchronous GPU status/error "
                  "reporting and host-buffer integration remain pending. This tool may wait because it is an "
                  "offline validator.\"\n}\n";
        return failed ? 1 : 0;
    }
}
