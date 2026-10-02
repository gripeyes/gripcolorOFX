#include "rendition/kernel_math.hpp"
using namespace rendition_kernel;
kernel void renditionPoints(device const float4 *src [[buffer(0)]], device float4 *dst [[buffer(1)]],
                            constant Parameters &p [[buffer(2)]], device const float *spectral [[buffer(3)]],
                            constant M3 &basis [[buffer(4)]], constant M3 &inverseBasis [[buffer(5)]],
                            device uint *status [[buffer(6)]], constant uint &count [[buffer(7)]],
                            uint id [[thread_position_in_grid]]) {
    if (id >= count)
        return;
    float4 input = src[id];
    status[id] = 0;
    if (p.identity) {
        dst[id] = input;
        return;
    }
    if (get(p, P_alphaMode) && input.w == 0) {
        dst[id] = input;
        return;
    }
    if (get(p, P_alphaMode) && !isfinite(input.w)) {
        status[id] = 2;
        dst[id] = input;
        return;
    }
    V3 rgb{input.x, input.y, input.z};
    if (get(p, P_alphaMode)) {
        rgb = mul(rgb, 1 / input.w);
        if (!finite3(rgb)) {
            status[id] = 2;
            dst[id] = input;
            return;
        }
    }
    Result r = run(p, rgb, spectral, basis, inverseBasis);
    if (get(p, P_alphaMode))
        r.rgb = mul(r.rgb, input.w);
    if (!finite3(r.rgb) && r.error == 0)
        r.error = 2;
    status[id] = r.error;
    dst[id] = float4(r.rgb.x, r.rgb.y, r.rgb.z, input.w);
}
