#pragma once
// Scalar equations shared verbatim between C++ reference and Metal. No fast math.
#ifdef __METAL_VERSION__
#include <metal_stdlib>
using namespace metal;
#define K_CONSTANT constant
#define K_DEVICE device
#else
#include <algorithm>
#include <cmath>
using std::abs;
using std::atan2;
using std::copysign;
using std::cos;
using std::exp;
using std::exp2;
using std::floor;
using std::isfinite;
using std::log;
using std::log1p;
using std::log2;
using std::pow;
using std::sin;
using std::sqrt;
using std::tanh;
#define K_CONSTANT
#define K_DEVICE
#endif
#include "kernel_parameters.hpp"
namespace rendition_kernel {
inline float mn(float a, float b) {
    return a < b ? a : b;
}
inline float mx(float a, float b) {
    return a > b ? a : b;
}
inline float clampf(float x, float lo, float hi) {
    return mn(mx(x, lo), hi);
}
inline float cubeRoot(float x) {
    return copysign(pow(abs(x), 1.f / 3.f), x);
}
struct V3 {
    float x, y, z;
};
inline V3 add(V3 a, V3 b) {
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}
inline V3 sub(V3 a, V3 b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}
inline V3 mul(V3 a, float s) {
    return {a.x * s, a.y * s, a.z * s};
}
inline float component(V3 a, int i) {
    return i == 0 ? a.x : i == 1 ? a.y : a.z;
}
inline V3 setComponent(V3 a, int i, float x) {
    if (i == 0)
        a.x = x;
    else if (i == 1)
        a.y = x;
    else
        a.z = x;
    return a;
}
inline bool finite3(V3 a) {
    return isfinite(a.x) && isfinite(a.y) && isfinite(a.z);
}
inline float length3(V3 a) {
    float scale = mx(abs(a.x), mx(abs(a.y), abs(a.z)));
    if (scale == 0)
        return 0;
    V3 q{a.x / scale, a.y / scale, a.z / scale};
    return scale * sqrt(q.x * q.x + q.y * q.y + q.z * q.z);
}
inline float length2(float x, float y) {
    return length3({x, y, 0});
}
struct M3 {
    float a[9];
};
inline V3 transform(M3 m, V3 x) {
    return {m.a[0] * x.x + m.a[1] * x.y + m.a[2] * x.z, m.a[3] * x.x + m.a[4] * x.y + m.a[5] * x.z,
            m.a[6] * x.x + m.a[7] * x.y + m.a[8] * x.z};
}
struct Parameters {
    float v[P_COUNT];
    M3 toXYZ, fromXYZ, toD65, fromD65, matrix, whiteBalance, inverseRecord;
    int effect, look, identity;
};
inline float get(K_CONSTANT const Parameters &p, int key) {
    return p.v[key];
}
inline float sigmoid(float x) {
    if (x >= 0)
        return 1 / (1 + exp(-x));
    float e = exp(x);
    return e / (1 + e);
}
inline float logOnePlus(float x) {
    return x < .01f ? x * (1 - x * .5f + x * x / 3 - x * x * x * .25f + x * x * x * x * .2f) : log(1 + x);
}
inline float softplus(float x) {
    return mx(x, 0) + logOnePlus(exp(-abs(x)));
}
inline float smooth(float a, float b, float x) {
    if (b <= a)
        return x >= b ? 1 : 0;
    float t = clampf((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
}
inline float wrap(float h) {
    return h - 360 * floor(h / 360);
}
inline float angularDistance(float a, float b) {
    float d = abs(wrap(a) - wrap(b));
    return mn(d, 360 - d);
}
inline float encode(float x, int d) {
    if (d == 0)
        return x > 0 ? log2(x / .18f) : NAN;
    if (d == 1)
        return x <= .0078125f ? 10.5402377416545f * x + .0729055341958355f : (log2(x) + 9.72f) / 17.52f;
    if (d == 2) {
        float a = (262144.f - 16.f) / 117.45f, b = 928.f / 1023.f, c = 95.f / 1023.f,
              s = 7.f * log(2.f) * exp2(7.f - 14.f * c / b) / (a * b),
              t = (exp2(14.f * (-c / b) + 6.f) - 64.f) / a;
        return x < t ? (x - t) / s : (log2(a * x + 64.f) - 6.f) / 14.f * b + c;
    }
    if (d == 3)
        return x <= .00262409f ? x * 10.44426855f : (log2(x + .0075f) + 7.f) * .07329248f;
    if (d == 4)
        return x > 0 ? (log2(x / .18f) + 10.f) / 16.5f : NAN;
    float b = .18f / 64.f;
    return x <= b ? -6.f + (x - b) / (b * log(2.f)) : log2(x / .18f);
}
inline float decode(float x, int d) {
    if (d == 0)
        return .18f * exp2(x);
    if (d == 1)
        return x <= .155251141552511f ? (x - .0729055341958355f) / 10.5402377416545f
                                      : exp2(x * 17.52f - 9.72f);
    if (d == 2) {
        float a = (262144.f - 16.f) / 117.45f, b = 928.f / 1023.f, c = 95.f / 1023.f,
              s = 7.f * log(2.f) * exp2(7.f - 14.f * c / b) / (a * b),
              t = (exp2(14.f * (-c / b) + 6.f) - 64.f) / a;
        return x < 0 ? x * s + t : (exp2(14.f * (x - c) / b + 6.f) - 64.f) / a;
    }
    if (d == 3)
        return x <= .02740668f ? x / 10.44426855f : exp2(x / .07329248f - 7.f) - .0075f;
    if (d == 4)
        return .18f * exp2(x * 16.5f - 10.f);
    float b = .18f / 64.f;
    return x <= -6.f ? b + (x + 6.f) * b * log(2.f) : .18f * exp2(x);
}
inline V3 encode3(V3 x, int d) {
    return {encode(x.x, d), encode(x.y, d), encode(x.z, d)};
}
inline V3 decode3(V3 x, int d) {
    return {decode(x.x, d), decode(x.y, d), decode(x.z, d)};
}
inline float slope(int d) {
    return d == 1   ? 1 / 17.52f
           : d == 2 ? 928.f / 1023.f / 14.f
           : d == 3 ? .07329248f
           : d == 4 ? 1 / 16.5f
                    : 1;
}
inline V3 opponent(V3 xyz) {
    M3 m{{.8189330101f, .3618667424f, -.1288597137f, .0329845436f, .9293118715f, .0361456387f, .0482003018f,
          .2643662691f, .6338517070f}};
    V3 l = transform(m, xyz);
    l = {cubeRoot(l.x), cubeRoot(l.y), cubeRoot(l.z)};
    M3 n{{.2104542553f, .7936177850f, -.0040720468f, 1.9779984951f, -2.4285922050f, .4505937099f,
          .0259040371f, .7827717662f, -.8086757660f}};
    return transform(n, l);
}
inline V3 opponentInverse(V3 lab) {
    // These inverses are generated from the exact forward coefficients, not separately rounded vendor
    // formulas.
    M3 m{{1.000000000f, .3963377922f, .2158037581f, 1.000000009f, -.1055613423f, -.06385417477f, 1.000000055f,
          -.08948418209f, -1.291485538f}};
    V3 l = transform(m, lab);
    l = {l.x * l.x * l.x, l.y * l.y * l.y, l.z * l.z * l.z};
    M3 n{{1.2270138511f, -.5577999807f, .2812561490f, -.0405801784f, 1.1122568696f, -.0716766787f,
          -.0763812845f, -.4214819784f, 1.5861632204f}};
    return transform(n, l);
}
inline float ev(K_CONSTANT const Parameters &p, V3 rgb) {
    float y = transform(p.toD65, transform(p.toXYZ, rgb)).y;
    return (encode(y, 1) - encode(.18f, 1)) / slope(1);
}
// Selection slots are supplied explicitly by generated parameter identifiers.
inline float selection(K_CONSTANT const Parameters &p, V3 lab, float exposure, int hue, int width, int cmin,
                       int cmax, int emin, int emax, int softness, int neutral) {
    float c = length2(lab.y, lab.z), relative = c / mx(abs(lab.x), 1e-12f),
          h = wrap(atan2(lab.z, lab.y) * 57.2957795131f), w = get(p, width), soft = get(p, softness),
          dist = angularDistance(h, get(p, hue));
    float hw = w >= 360 ? 1 : 1 - smooth(.5f * w * (1 - soft), .5f * w, dist),
          cr = mx(get(p, cmax) - get(p, cmin), .001f), er = mx(get(p, emax) - get(p, emin), .1f);
    float cw = (get(p, cmin) == 0 ? 1 : smooth(get(p, cmin) - cr * soft * .5f, get(p, cmin), relative)) *
               (1 - smooth(get(p, cmax), get(p, cmax) + cr * soft * .5f, relative));
    float ew = smooth(get(p, emin) - er * soft * .5f, get(p, emin), exposure) *
               (1 - smooth(get(p, emax), get(p, emax) + er * soft * .5f, exposure));
    return hw * cw * ew * smooth(0, mx(get(p, neutral), 1e-5f), relative);
}
inline V3 deform(V3 lab, float hue, float chroma, float density, float exposure) {
    float a = hue * .017453292519943f, cs = cos(a), sn = sin(a), ls = exp2(exposure / 3 - density / 3),
          cc = chroma * exp2(exposure / 3 + density * .15f);
    return {lab.x * ls, (lab.y * cs - lab.z * sn) * cc, (lab.y * sn + lab.z * cs) * cc};
}
inline float tone(K_CONSTANT const Parameters &p, float z, float contrast) {
    float q = z - get(p, P_pivot);
    return get(p, P_pivot) +
           contrast * (q + get(p, P_toe) * softplus(-q - get(p, P_toeExtent)) -
                       get(p, P_shoulder) * softplus(q - get(p, P_shoulderExtent))) -
           .15f * contrast *
               (get(p, P_shadowDensity) * sigmoid(-z - get(p, P_toeExtent)) +
                get(p, P_highlightDensity) * sigmoid(z - get(p, P_shoulderExtent)));
}
inline M3 spectralMatrix(K_DEVICE const float *table, int model, float hue, float density) {
    const float hues[6] = {29, 110, 145, 195, 265, 325};
    float h = wrap(hue);
    int a = 5, b = 0;
    float begin = hues[5], end = hues[0] + 360;
    if (h < hues[0])
        h += 360;
    for (int i = 0; i < 5; i++)
        if (h >= hues[i] && h < hues[i + 1]) {
            a = i;
            b = i + 1;
            begin = hues[a];
            end = hues[b];
            break;
        }
    float ht = (h - begin) / (end - begin), z = clampf(density, 0, 1) * 128;
    int k = int(mn(floor(z), 127));
    float dt = z - k;
    M3 m;
    for (int j = 0; j < 9; j++) {
        int ia = ((model * 6 + a) * 129 + k) * 9 + j, ib = ((model * 6 + b) * 129 + k) * 9 + j;
        m.a[j] = (1 - ht) * ((1 - dt) * table[ia] + dt * table[ia + 9]) +
                 ht * ((1 - dt) * table[ib] + dt * table[ib + 9]);
    }
    return m;
}
inline V3 positive(V3 c) {
    float e = .001f * length3(c);
    return {.5f * (c.x + length2(c.x, e)), .5f * (c.y + length2(c.y, e)), .5f * (c.z + length2(c.z, e))};
}
struct Result {
    V3 rgb;
    int error;
};
// error: 0 OK; 1 nonfinite source; 2 domain/overflow; 3 geometry required.
inline Result run(K_CONSTANT const Parameters &p, V3 rgb, K_DEVICE const float *spectral, M3 B, M3 inverseB) {
    if (p.identity)
        return {rgb, 0};
    if (p.effect == 7) {
        int mode = int(get(p, P_mode));
        if (mode == 9) {
            bool outside = rgb.x < 0 || rgb.y < 0 || rgb.z < 0 || rgb.x > 1 || rgb.y > 1 || rgb.z > 1;
            return {outside ? V3{1, 0, 1} : V3{0, 0, 0}, 0};
        }
        if (mode == 10)
            return {finite3(rgb) ? V3{0, 0, 0} : V3{1, 0, 0}, 0};
        return {rgb, 3};
    }
    if (!finite3(rgb))
        return {rgb, 1};
    V3 out = rgb;
    if (p.effect == 0) {
        const int exposures[3] = {P_rExposure, P_gExposure, P_bExposure},
                  slopes[3] = {P_rSlope, P_gSlope, P_bSlope}, offsets[3] = {P_rOffset, P_gOffset, P_bOffset},
                  powers[3] = {P_rPower, P_gPower, P_bPower};
        for (int i = 0; i < 3; i++)
            out = setComponent(out, i, component(out, i) * exp2(get(p, P_exposure) + get(p, exposures[i])));
        out = transform(p.whiteBalance, out);
        out = add(out, mul(sub(transform(p.matrix, out), out), get(p, P_matrixMix)));
        if (get(p, P_cdlDomain))
            out = encode3(out, p.look);
        for (int i = 0; i < 3; i++) {
            float x = component(out, i) * get(p, slopes[i]) + get(p, offsets[i]);
            out = setComponent(out, i, copysign(pow(abs(x), get(p, powers[i])), x));
        }
        if (get(p, P_saturation) != 1) {
            float l = transform(p.toXYZ, out).y;
            out = add(mul(out, get(p, P_saturation)), mul({l, l, l}, 1 - get(p, P_saturation)));
        }
        if (get(p, P_cdlDomain))
            out = decode3(out, p.look);
    } else if (p.effect == 1) {
        V3 exposed = mul(rgb, exp2(get(p, P_exposure))), q = encode3(exposed, p.look);
        float g = encode(.18f, p.look), a = slope(p.look);
        if (get(p, P_linked) == 0) {
            float envelope = mx(abs(exposed.x), mx(abs(exposed.y), abs(exposed.z)));
            float z = (encode(envelope, p.look) - g) / a, dz = tone(p, z, get(p, P_contrast)) - z;
            if (get(p, P_preserveGray))
                dz -= tone(p, 0, get(p, P_contrast));
            q = add(q, {a * dz, a * dz, a * dz});
        } else {
            const int cc[3] = {P_rContrast, P_gContrast, P_bContrast};
            for (int i = 0; i < 3; i++) {
                float z = (component(q, i) - g) / a, c = get(p, P_contrast) * get(p, cc[i]),
                      f = tone(p, z, c);
                if (get(p, P_preserveGray))
                    f -= tone(p, 0, c);
                q = setComponent(q, i, g + a * f);
            }
        }
        out = decode3(q, p.look);
    } else if (p.effect == 5) {
        out = get(p, P_domain) ? decode3(transform(p.matrix, encode3(rgb, p.look)), p.look)
                               : transform(p.matrix, rgb);
    } else if (p.effect == 2 || p.effect == 4) {
        V3 lab = opponent(transform(p.toD65, transform(p.toXYZ, rgb))), sum{0, 0, 0}, rgbDelta{0, 0, 0};
        float exposure = ev(p, rgb), total = 0, fh = 0, fc = 0, fd = 0, fe = 0;
        if (p.effect == 2) {
            int debug = int(get(p, P_debug));
            for (int i = 0; i < 6; i++) {
                int base = P_v0_chroma + i * (P_v1_chroma - P_v0_chroma);
#define RK(key) (base + P_v0_##key - P_v0_chroma)
                float w = selection(p, lab, exposure, RK(hue), RK(width), RK(chromaMin), RK(chromaMax),
                                    RK(evMin), RK(evMax), RK(softness), RK(neutral));
                if (debug == i + 2)
                    return {{w, w, w}, 0};
                bool active = get(p, RK(hueDelta)) != 0 || get(p, RK(chroma)) != 1 ||
                              get(p, RK(density)) != 0 || get(p, RK(exposure)) != 0 ||
                              get(p, RK(matrixMix)) != 0;
                if (debug == 1 || active)
                    total += w;
                if (!active)
                    continue;
                sum = add(sum, mul(sub(deform(lab, get(p, RK(hueDelta)), get(p, RK(chroma)),
                                              get(p, RK(density)), get(p, RK(exposure))),
                                       lab),
                                   w));
                M3 m;
                for (int j = 0; j < 9; j++)
                    m.a[j] = get(p, RK(m00) + j);
                rgbDelta = add(rgbDelta, mul(sub(transform(m, rgb), rgb), w * get(p, RK(matrixMix))));
                fh += w * get(p, RK(hueDelta));
                fc += w * log(mx(get(p, RK(chroma)), 1e-6f));
                fd += w * get(p, RK(density));
                fe += w * get(p, RK(exposure));
#undef RK
            }
            if (debug == 1) {
                float w = mn(total, 1);
                return {{w, w, w}, 0};
            }
            if (total == 0)
                return {rgb, 0};
            float norm = mx(1, total);
            int overlap = int(get(p, P_overlap));
            if (overlap == 1) {
                sum = mul(sum, 1 / norm);
                rgbDelta = mul(rgbDelta, 1 / norm);
            }
            if (overlap == 2) {
                float bound = mx(abs(lab.x), .001f), len = length3(sum);
                if (len > 0)
                    sum = mul(sum, bound * tanh(len / bound) / len);
                rgbDelta = mul(rgbDelta, 1 / norm);
            }
            if (overlap == 3) {
                sum = sub(deform(lab, fh / norm, exp(fc / norm), fd / norm, fe / norm), lab);
                rgbDelta = mul(rgbDelta, 1 / norm);
            }
            out = add(transform(p.fromXYZ, transform(p.fromD65, opponentInverse(add(lab, sum)))), rgbDelta);
        } else if (get(p, P_mode) == 0) {
            float d = 1 - sigmoid((exposure - get(p, P_darkPivot)) / get(p, P_transition)),
                  b = sigmoid((exposure - get(p, P_brightPivot)) / get(p, P_transition)), m = 1 - d - b;
            float hue = d * get(p, P_darkHue) + m * get(p, P_midHue) + b * get(p, P_brightHue),
                  ch = d * get(p, P_darkChroma) + m * get(p, P_midChroma) + b * get(p, P_brightChroma),
                  dn = d * get(p, P_darkDensity) + m * get(p, P_midDensity) + b * get(p, P_brightDensity);
            float w = selection(p, lab, exposure, P_hue, P_width, P_chromaMin, P_chromaMax, P_evMin, P_evMax,
                                P_softness, P_neutral);
            if (w == 0)
                return {rgb, 0};
            out = transform(p.fromXYZ,
                            transform(p.fromD65, opponentInverse(add(
                                                     lab, mul(sub(deform(lab, hue, ch, dn, 0), lab), w)))));
        } else {
            V3 q = encode3(rgb, p.look);
            float a = slope(p.look), g = encode(.18f, p.look);
            const int dark[3] = {P_darkr, P_darkg, P_darkb}, mid[3] = {P_midr, P_midg, P_midb},
                      bright[3] = {P_brightr, P_brightg, P_brightb};
            for (int i = 0; i < 3; i++) {
                float z = (component(q, i) - g) / a,
                      d = 1 - sigmoid((z - get(p, P_darkPivot)) / get(p, P_transition)),
                      b = sigmoid((z - get(p, P_brightPivot)) / get(p, P_transition)), m = 1 - d - b;
                q = setComponent(q, i,
                                 component(q, i) +
                                     a * (d * get(p, dark[i]) + m * get(p, mid[i]) + b * get(p, bright[i])));
            }
            out = decode3(q, p.look);
        }
    } else if (p.effect == 3 || p.effect == 6) {
        V3 xyz = transform(p.toD65, transform(p.toXYZ, rgb)), lab = opponent(xyz);
        float c = length2(lab.y, lab.z), relative = c / mx(abs(lab.x), 1e-12f),
              hue = wrap(atan2(lab.z, lab.y) * 57.2957795131f);
        V3 coeff = transform(inverseB, xyz), pos = positive(coeff), residual = sub(xyz, transform(B, pos)),
           candidate = xyz;
        if (p.effect == 3) {
            float exposure = ev(p, rgb), w = selection(p, lab, exposure, P_hue, P_width, P_chromaMin,
                                                       P_chromaMax, P_evMin, P_evMax, P_softness, P_neutral);
            w *= 1 - get(p, P_highlightProtection) * sigmoid((exposure - 3) / 2);
            w *= 1 - get(p, P_shadowWeight) + get(p, P_shadowWeight) * sigmoid((-exposure + 2) / 2);
            if (get(p, P_debug))
                return {{w, w, w}, 0};
            float d = get(p, P_density);
            if (w == 0 || d == 0)
                return {rgb, 0};
            V3 filtered = add(transform(spectralMatrix(spectral, 0, hue, abs(d)), pos), residual);
            candidate = add(xyz, mul(sub(filtered, xyz), copysign(1.f, d)));
            V3 q = opponent(candidate);
            float qc = length2(q.y, q.z), target = c * exp2(d * get(p, P_chromaCoupling));
            if (qc > 1e-12f) {
                q.y *= target / qc;
                q.z *= target / qc;
            }
            candidate = add(xyz, mul(sub(opponentInverse(q), xyz), w));
        } else {
            float amount = get(p, P_separation), leak = get(p, P_leakage) * amount,
                  mean = (pos.x + pos.y + pos.z) / 3;
            V3 separated = add(mul(pos, 1 - leak), mul({mean, mean, mean}, leak));
            if (get(p, P_mode) == 1) {
                float mid = separated.y;
                separated.y = 0;
                separated.x += mid * .5f;
                separated.z += mid * .5f;
            }
            if (get(p, P_mode) == 2)
                separated = transform(p.matrix, separated);
            V3 positiveRecord = positive(separated), recordResidual = sub(separated, positiveRecord);
            float recordSum = positiveRecord.x + positiveRecord.y + positiveRecord.z;
            if (recordSum > 0 && get(p, P_palette) != 0) {
                float power = exp2(amount * get(p, P_palette));
                V3 shape{pow(positiveRecord.x / recordSum, power),
                         pow(positiveRecord.y / recordSum, power),
                         pow(positiveRecord.z / recordSum, power)};
                positiveRecord = mul(shape, recordSum / (shape.x + shape.y + shape.z));
            }
            positiveRecord.x *= get(p, P_bContribution);
            positiveRecord.y *= get(p, P_gContribution);
            positiveRecord.z *= get(p, P_rContribution);
            float d = amount * (.6f + .4f * get(p, P_density));
            V3 filtered = transform(spectralMatrix(spectral, 1, hue, d), positiveRecord),
               recombined = add(transform(inverseB, filtered), recordResidual);
            recombined.x *= get(p, P_bWeight);
            recombined.y *= get(p, P_gWeight);
            recombined.z *= get(p, P_rWeight);
            if (get(p, P_mode) == 2)
                recombined = transform(p.inverseRecord, recombined);
            V3 reconstructed = add(transform(B, recombined), residual);
            float neutral = 1 - get(p, P_neutralAnchor) + get(p, P_neutralAnchor) * smooth(0, .05f, relative),
                  red = 1 - get(p, P_redAnchor) * (1 - smooth(20, 70, angularDistance(hue, 29)));
            candidate = add(xyz, mul(sub(reconstructed, xyz), amount * neutral * red * get(p, P_mix)));
        }
        out = transform(p.fromXYZ, transform(p.fromD65, candidate));
    }
    return {out, finite3(out) ? 0 : 2};
}
} // namespace rendition_kernel
#undef K_CONSTANT
#undef K_DEVICE
