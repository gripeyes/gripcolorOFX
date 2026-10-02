#include "rendition/operators.hpp"
#include "rendition/kernel_bridge.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
namespace rendition {
const char *name(Effect e) {
    static const char *n[] = {"Scene",     "Tone",      "Volume", "Density",
                              "Crossover", "Crosstalk", "Strip",  "Inspector"};
    int i = int(e);
    if (i < 0 || i > 7)
        throw std::invalid_argument("Invalid effect");
    return n[i];
}
std::vector<Parameter> parameters(Effect e) {
    if (int(e) < 0 || int(e) > int(Effect::Inspector))
        throw std::invalid_argument("Unknown effect identifier");
    std::vector<Parameter> p;
    auto add = [&](std::string id, std::string label, double v, double lo, double hi,
                   std::string group = "Artist", std::string unit = "",
                   std::vector<std::string> choices = {}) {
        p.push_back({id, label, group, unit, v, lo, hi, choices});
    };
    add("interpretation", "Source interpretation", 0, 0, 4, "Input", "",
        {"Auto / interpretation required", "Linear Rec.2020", "ACEScg / AP1", "Linear Rec.709",
         "Custom xy primaries / white"});
    add("alphaMode", "RGB / alpha handling", 0, 0, 1, "Input", "",
        {"RGB as supplied", "Unpremultiply / process / premultiply"});
    const char *cn[] = {"rx", "ry", "gx", "gy", "bx", "by", "wx", "wy"};
    double cv[] = {.708, .292, .170, .797, .131, .046, .3127, .329};
    for (int i = 0; i < 8; i++)
        add(cn[i], cn[i], cv[i], 0, 1, "Custom primaries", "xy");
    add("modelVersion", "Mathematical model", 0, 0, 0, "Expert", "", {"v1 research candidate"});
    add("adapterVersion", "Signed adapter", 0, 0, 0, "Expert", "", {"v1 documented per model"});
    if (e == Effect::Scene || e == Effect::Tone || e == Effect::Crossover || e == Effect::Crosstalk)
        add("lookDomain", "Look coordinate encoding", 1, 0, 5, "Expert", "",
            {"Pure stops (positive only)", "ACEScct scalar encoding", "LogC4 scalar encoding",
             "DaVinci Intermediate scalar encoding", "AgX unclamped stops (positive only)",
             "LookLog candidate"});
    auto matrix = [&](std::string group) {
        for (int i = 0; i < 3; i++)
            for (int j = 0; j < 3; j++)
                add("m" + std::to_string(i) + std::to_string(j),
                    "M" + std::to_string(i + 1) + std::to_string(j + 1), i == j ? 1 : 0, -8, 8, group,
                    "coefficient");
    };
    if (e == Effect::Scene) {
        add("exposure", "Exposure", 0, -20, 20, "Artist", "stops");
        for (auto c : {"r", "g", "b"})
            add(std::string(c) + "Exposure", std::string(c) + " exposure", 0, -20, 20, "Artist", "stops");
        add("temperature", "Illuminant estimate (daylight)", 6504, 4000, 25000, "Artist", "K");
        add("tint", "Illuminant tint", 0, -.05, .05, "Artist", "CIE v offset");
        add("adaptation", "Chromatic adaptation", 0, 0, 2, "Expert", "",
            {"Bradford", "CAT16", "XYZ scaling"});
        matrix("Custom matrix");
        add("matrixMix", "Matrix mix", 0, 0, 1, "Custom matrix", "fraction");
        add("cdlDomain", "SOP / saturation domain", 0, 0, 1, "Expert", "",
            {"Scene Linear", "Selected look coordinate"});
        for (auto c : {"r", "g", "b"}) {
            add(std::string(c) + "Slope", std::string(c) + " slope", 1, 0, 8, "SOP", "factor");
            add(std::string(c) + "Offset", std::string(c) + " offset", 0, -4, 4, "SOP", "domain units");
            add(std::string(c) + "Power", std::string(c) + " signed power", 1, .05, 8, "SOP", "exponent");
        }
        add("saturation", "Saturation", 1, 0, 4, "SOP", "factor");
    }
    if (e == Effect::Tone) {
        add("exposure", "Exposure", 0, -20, 20, "Artist", "stops");
        add("contrast", "Contrast", 1, .05, 4, "Artist", "factor");
        add("pivot", "Pivot relative to 0.18", 0, -12, 12, "Artist", "stops");
        add("toe", "Toe strength", 0, 0, .8, "Artist", "fraction");
        add("toeExtent", "Toe extent", 4, .1, 20, "Artist", "stops");
        add("shoulder", "Shoulder strength", 0, 0, .8, "Artist", "fraction");
        add("shoulderExtent", "Shoulder extent", 4, .1, 20, "Artist", "stops");
        add("shadowDensity", "Shadow density", 0, -1, 1, "Artist", "stops");
        add("highlightDensity", "Highlight density", 0, -1, 1, "Artist", "stops");
        add("preserveGray", "Preserve middle gray (excluding exposure)", 1, 0, 1, "Artist", "",
            {"Off", "On"});
        add("linked", "Channel mode", 0, 0, 1, "Artist", "",
            {"Linked coordinate displacement", "Per-channel"});
        for (auto c : {"r", "g", "b"})
            add(std::string(c) + "Contrast", std::string(c) + " contrast", 1, .05, 4, "Channels", "factor");
    }
    auto range = [&](std::string prefix, std::string group, double hue) {
        add(prefix + "hue", "Hue center", hue, 0, 360, group, "degrees");
        add(prefix + "width", "Hue width", 90, .1, 360, group, "degrees");
        add(prefix + "chromaMin", "Minimum relative chroma", 0, 0, 4, group, "C / |L|");
        add(prefix + "chromaMax", "Maximum relative chroma", 4, 0, 4, group, "C / |L|");
        add(prefix + "evMin", "Minimum exposure", -20, -30, 30, group, "stops");
        add(prefix + "evMax", "Maximum exposure", 20, -30, 30, group, "stops");
        add(prefix + "softness", "Selection softness", .5, .01, 1, group, "fraction");
        add(prefix + "neutral", "Neutral protection", .03, 0, .5, group, "C / |L|");
    };
    if (e == Effect::Volume) {
        const char *families[] = {"Red", "Yellow", "Green", "Cyan", "Blue", "Magenta"};
        double hues[] = {29, 110, 145, 195, 265, 325};
        for (int i = 0; i < 6; i++) {
            std::string k = "v" + std::to_string(i) + "_", g = families[i];
            range(k, g, hues[i]);
            add(k + "hueDelta", "Hue displacement", 0, -180, 180, g, "degrees");
            add(k + "chroma", "Chroma scale", 1, 0, 4, g, "factor");
            add(k + "density", "Density (coordinate trajectory)", 0, -2, 2, g, "artistic units");
            add(k + "exposure", "Exposure displacement", 0, -8, 8, g, "stops");
            for (int a = 0; a < 3; a++)
                for (int b = 0; b < 3; b++)
                    add(k + "m" + std::to_string(a) + std::to_string(b),
                        "Local M" + std::to_string(a + 1) + std::to_string(b + 1), a == b ? 1 : 0, -4, 4, g,
                        "coefficient");
            add(k + "matrixMix", "Local matrix mix", 0, 0, 1, g, "fraction");
        }
        add("overlap", "Overlap composition", 1, 0, 3, "Expert", "",
            {"Weighted deltas", "Normalized weighted deltas", "Bounded vector accumulation", "Shared field"});
        add("debug", "Selection view", 0, 0, 7, "Diagnostic", "",
            {"Off", "Combined weight", "Red", "Yellow", "Green", "Cyan", "Blue", "Magenta"});
    }
    if (e == Effect::Density) {
        range("", "Selection", 195);
        for (auto &d : p)
            if (d.id == "width")
                d.value = 360;
        add("density", "Density", 0, -1, 1, "Artist", "artistic units");
        add("chromaCoupling", "Chroma-density coupling", 0, -1, 1, "Artist", "factor");
        add("highlightProtection", "Highlight protection", .5, 0, 1, "Artist", "fraction");
        add("shadowWeight", "Shadow weighting", .5, 0, 1, "Artist", "fraction");
        add("debug", "Density-only view", 0, 0, 1, "Diagnostic", "", {"Off", "Weight"});
    }
    if (e == Effect::Crossover) {
        add("mode", "Crossover mode", 0, 0, 1, "Artist", "", {"Hue trajectories", "Channel trajectories"});
        range("", "Selection", 195);
        add("darkPivot", "Dark transition center", -3, -20, 20, "Artist", "stops");
        add("brightPivot", "Bright transition center", 3, -20, 20, "Artist", "stops");
        add("transition", "Transition width", 2, .1, 10, "Artist", "stops");
        for (auto band : {"dark", "mid", "bright"}) {
            add(std::string(band) + "Hue", std::string(band) + " hue displacement", 0, -180, 180, "Artist",
                "degrees");
            add(std::string(band) + "Chroma", std::string(band) + " chroma scale", 1, 0, 4, "Artist",
                "factor");
            add(std::string(band) + "Density", std::string(band) + " density", 0, -2, 2, "Artist",
                "artistic units");
            for (auto c : {"r", "g", "b"})
                add(std::string(band) + c, std::string(band) + " " + c + " displacement", 0, -4, 4,
                    "Channels", "normalized look stops");
        }
    }
    if (e == Effect::Crosstalk) {
        matrix("Matrix");
        add("mode", "Matrix constraints", 1, 0, 3, "Artist", "",
            {"Unrestricted", "Neutral-preserving (row sums = 1)", "Row-sum locked", "Luminance preserving"});
        add("domain", "Processing domain", 0, 0, 1, "Artist", "",
            {"Scene Linear", "Selected look coordinate"});
        add("rowSum", "Locked row sum", 1, -4, 4, "Expert", "factor");
        add("mix", "Mix", 1, 0, 1, "Artist", "fraction");
        for (auto k : {"rg", "rb", "gr", "gb", "br", "bg"})
            add(k, std::string(k) + " interaction", 0, -2, 2, "Artist", "coefficient");
    }
    if (e == Effect::Strip) {
        add("mode", "Separation system", 0, 0, 2, "Artist", "",
            {"Three-channel", "Two-channel", "Custom basis"});
        add("separation", "Separation", 0, 0, 1, "Artist", "fraction");
        add("leakage", "Leakage", .1, 0, 1, "Artist", "fraction");
        add("density", "Dye density coupling", 0, -1, 1, "Artist", "artistic units");
        add("palette", "Palette compression / expansion", 0, -1, 1, "Artist", "artistic units");
        add("neutralAnchor", "Neutral anchor", 1, 0, 1, "Artist", "fraction");
        add("redAnchor", "Red / skin anchor", 0, 0, 1, "Artist", "fraction");
        add("mix", "Global mix", 1, 0, 1, "Artist", "fraction");
        for (auto c : {"r", "g", "b"}) {
            add(std::string(c) + "Contribution", std::string(c) + " separation contribution", 1, 0, 2,
                "Artist", "factor");
            add(std::string(c) + "Weight", std::string(c) + " recombination weight", 1, 0, 2, "Artist",
                "factor");
        }
        matrix("Custom basis");
    }
    if (e == Effect::Inspector) {
        add("mode", "Diagnostic", 0, 0, 10, "Artist", "",
            {"Input", "Exposure ramp", "Neutral ramp", "RGB ramps", "Hue sweep", "Chroma sweep",
             "Reference chart", "Color cube slice", "Difference vs Reference", "Out of nominal RGB gamut",
             "NaN / Inf"});
        add("evMin", "Minimum exposure", -12, -30, 30, "Artist", "stops");
        add("evMax", "Maximum exposure", 12, -30, 30, "Artist", "stops");
        add("slice", "Cube slice blue", .5, 0, 4, "Artist", "linear RGB");
    }
    if (e == Effect::Volume) {
        for (auto &d : p) {
            if (d.id.size() < 4 || d.id[0] != 'v' || d.id[2] != '_')
                continue;
            auto key = d.id.substr(3);
            if (key == "matrixMix" || (key.size() == 3 && key[0] == 'm'))
                d.group += " matrix";
            else if (key == "chromaMin" || key == "chromaMax" || key == "evMin" || key == "evMax" ||
                     key == "softness")
                d.group += " selection";
        }
    }
    return p;
}
namespace {
Mat3 readMatrix(const Snapshot &s, const std::string &prefix = "") {
    Mat3 m;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            m.v[i * 3 + j] = s.get(prefix + "m" + std::to_string(i) + std::to_string(j));
    return m;
}
} // namespace
Vec3 oklab(Vec3 xyz) {
    auto q = rendition_kernel::opponent({xyz.x, xyz.y, xyz.z});
    return {q.x, q.y, q.z};
}
Vec3 oklabInverse(Vec3 lab) {
    auto q = rendition_kernel::opponentInverse({lab.x, lab.y, lab.z});
    return {q.x, q.y, q.z};
}
float Snapshot::get(const std::string &key) const {
    auto i = values.find(key);
    if (i == values.end())
        throw std::invalid_argument("Unknown parameter: " + key);
    return float(i->second);
}
Snapshot::Snapshot(Effect e, const Values &v, const std::string &metadata)
    : effect(e), space(ColorSpace::make(Gamut::Rec2020)) {
    auto defs = parameters(e);
    for (auto &p : defs)
        values[p.id] = p.value;
    for (auto &item : v) {
        const auto &k = item.first;
        double val = item.second;
        auto it = std::find_if(defs.begin(), defs.end(), [&](auto &p) { return p.id == k; });
        if (it == defs.end())
            throw std::invalid_argument("Unknown parameter: " + k);
        if (!std::isfinite(val) || val < it->lo || val > it->hi ||
            (!it->choices.empty() && val != std::floor(val)))
            throw std::invalid_argument("Invalid parameter: " + k);
        values[k] = val;
    }
    space =
        interpret(int(get("interpretation")), metadata,
                  {get("rx"), get("ry"), get("gx"), get("gy"), get("bx"), get("by"), get("wx"), get("wy")});
    look = values.count("lookDomain") ? static_cast<LookDomain>(int(get("lookDomain"))) : LookDomain::ACEScct;
    toD65 = adaptation(space.wx, space.wy, .3127, .3290);
    fromD65 = toD65.inverse();
    for (auto &p : defs)
        if (p.id.size() >= 9 && p.id.substr(p.id.size() - 9) == "chromaMin") {
            auto k = p.id.substr(0, p.id.size() - 9);
            if (get(k + "chromaMin") > get(k + "chromaMax") || get(k + "evMin") > get(k + "evMax"))
                throw std::invalid_argument("Selection minimum exceeds maximum");
        }
    if (e == Effect::Crossover && get("darkPivot") > get("brightPivot"))
        throw std::invalid_argument("Crossover dark pivot exceeds bright pivot");
    matrix = Mat3{};
    if (e == Effect::Scene || e == Effect::Crosstalk || e == Effect::Strip)
        matrix = readMatrix(*this);
    if (e == Effect::Crosstalk) {
        const char *names[] = {"rg", "rb", "gr", "gb", "br", "bg"};
        int rows[] = {0, 0, 1, 1, 2, 2}, cols[] = {1, 2, 0, 2, 0, 1};
        for (int n = 0; n < 6; n++) {
            double a = get(names[n]);
            matrix.v[rows[n] * 3 + cols[n]] += a;
            matrix.v[rows[n] * 3 + rows[n]] -= a;
        }
        int mode = int(get("mode"));
        if (mode == 1 || mode == 2) {
            for (int i = 0; i < 3; i++) {
                double sum = 0;
                for (int j = 0; j < 3; j++)
                    sum += matrix.v[i * 3 + j];
                matrix.v[i * 3 + i] += (mode == 1 ? 1 : get("rowSum")) - sum;
            }
        }
        if (mode == 3) {
            for (int j = 0; j < 3; j++) {
                double y = 0;
                for (int i = 0; i < 3; i++)
                    y += space.toXYZ.v[3 + i] * matrix.v[i * 3 + j];
                double d =
                    (space.toXYZ.v[3 + j] - y) / (space.toXYZ.v[3] + space.toXYZ.v[4] + space.toXYZ.v[5]);
                for (int i = 0; i < 3; i++)
                    matrix.v[i * 3 + j] += d;
            }
        }
        float mix = get("mix");
        for (int i = 0; i < 9; i++)
            matrix.v[i] = mix * matrix.v[i] + (1 - mix) * (i % 4 == 0 ? 1 : 0);
    }
    // Identity means effective operator identity, not merely an untouched parameter panel.
    identity = true;
    auto changed = [&](const std::string &k, double defaultValue) {
        if (values.count(k) && get(k) != defaultValue)
            identity = false;
    };
    if (e == Effect::Scene) {
        for (auto k : {"exposure", "rExposure", "gExposure", "bExposure", "tint"})
            changed(k, 0);
        changed("temperature", 6504);
        if (get("matrixMix") != 0)
            for (int i = 0; i < 9; i++)
                if (matrix.v[i] != (i % 4 == 0 ? 1 : 0))
                    identity = false;
        for (auto c : {"r", "g", "b"}) {
            changed(std::string(c) + "Slope", 1);
            changed(std::string(c) + "Offset", 0);
            changed(std::string(c) + "Power", 1);
        }
        changed("saturation", 1);
    }
    if (e == Effect::Tone) {
        for (auto k : {"exposure", "toe", "shoulder", "shadowDensity", "highlightDensity"})
            changed(k, 0);
        changed("contrast", 1);
        if (get("linked"))
            for (auto c : {"r", "g", "b"})
                changed(std::string(c) + "Contrast", 1);
    }
    if (e == Effect::Crosstalk)
        for (int i = 0; i < 9; i++)
            if (matrix.v[i] != (i % 4 == 0 ? 1 : 0))
                identity = false;
    if (e == Effect::Volume) {
        for (int i = 0; i < 6; i++) {
            auto k = "v" + std::to_string(i) + "_";
            for (auto t : {"hueDelta", "density", "exposure"})
                changed(k + t, 0);
            changed(k + "chroma", 1);
            if (get(k + "matrixMix") != 0)
                identity = false;
        }
        changed("debug", 0);
    }
    if (e == Effect::Crossover) {
        if (get("mode") == 0) {
            for (auto b : {"dark", "mid", "bright"}) {
                changed(std::string(b) + "Hue", 0);
                changed(std::string(b) + "Chroma", 1);
                changed(std::string(b) + "Density", 0);
            }
        } else
            for (auto b : {"dark", "mid", "bright"})
                for (auto c : {"r", "g", "b"})
                    changed(std::string(b) + c, 0);
    }
    if (e == Effect::Density) {
        changed("density", 0);
        changed("debug", 0);
    }
    if (e == Effect::Strip) {
        identity = get("separation") == 0 || get("mix") == 0;
    }
    if (e == Effect::Inspector)
        identity = get("mode") == 0;
    kernel = std::make_shared<const rendition_kernel::Parameters>(kernelParameters(*this));
}
Vec3 Snapshot::apply(Vec3 rgb) const {
    return kernelApply(*this, rgb);
}
std::array<float, 4> Snapshot::pixel(std::array<float, 4> p) const {
    if (identity)
        return p;
    Vec3 rgb{p[0], p[1], p[2]};
    if (get("alphaMode") && p[3] == 0)
        return p;
    if (get("alphaMode") && !std::isfinite(p[3]))
        throw std::domain_error("Nonfinite alpha");
    if (get("alphaMode")) {
        rgb = rgb * (1 / p[3]);
        if (!finite(rgb))
            throw std::overflow_error("Unpremultiplication produced nonfinite RGB");
    }
    rgb = apply(rgb);
    if (get("alphaMode"))
        rgb = rgb * p[3];
    if (!finite(rgb))
        throw std::overflow_error("Premultiplication produced nonfinite RGB");
    return {rgb.x, rgb.y, rgb.z, p[3]};
}
float *ImageView::at(int x, int y) const {
    if (!data || x < x1 || x >= x2 || y < y1 || y >= y2)
        return nullptr;
    return reinterpret_cast<float *>(reinterpret_cast<char *>(data) + ptrdiff_t(y - y1) * rowBytes) +
           ptrdiff_t(x - x1) * components;
}
void renderWindow(const Snapshot &s, const ImageView &src, const ImageView &dst, int x1, int y1, int x2,
                  int y2) {
    if ((src.components != 3 && src.components != 4) || (dst.components != 3 && dst.components != 4))
        throw std::invalid_argument("Only float RGB/RGBA supported");
    if (x1 < dst.x1 || y1 < dst.y1 || x2 > dst.x2 || y2 > dst.y2 || x2 < x1 || y2 < y1)
        throw std::invalid_argument("Invalid render window");
    for (int y = y1; y < y2; y++)
        for (int x = x1; x < x2; x++) {
            auto a = src.at(x, y), b = dst.at(x, y);
            std::array<float, 4> p =
                a ? std::array<float, 4>{a[0], a[1], a[2], src.components == 4 ? a[3] : 1}
                  : std::array<float, 4>{0, 0, 0, 0};
            auto q = s.pixel(p);
            if (s.isIdentity() && a && src.components == dst.components) {
                std::memcpy(b, a, size_t(dst.components) * sizeof(float));
            } else {
                b[0] = q[0];
                b[1] = q[1];
                b[2] = q[2];
                if (dst.components == 4)
                    b[3] = q[3];
            }
        }
}
Semantic semantics(Effect e, const Values &v) {
    auto val = [&](std::string k, double d) {
        auto i = v.find(k);
        return i == v.end() ? d : i->second;
    };
    Semantic s{"Scene Linear",
               "Scene-compatible rendition",
               "Conditioned",
               "Non-invertible",
               "Unbounded",
               "Native",
               "Exposure-conditioned",
               "Configuration-dependent",
               "Not promised",
               "Gamut-relative",
               "Research candidate",
               "No production host/artist acceptance; float overflow reports error"};
    if (e == Effect::Scene) {
        s.domain = val("cdlDomain", 0) ? "Look / Log" : "Scene Linear";
        s.exposure = "Equivariant";
        for (auto c : {"r", "g", "b"})
            if (val(std::string(c) + "Offset", 0) != 0 || val(std::string(c) + "Power", 1) != 1)
                s.exposure = "Non-equivariant";
        if (val("cdlDomain", 0) && (val("rSlope", 1) != 1 || val("gSlope", 1) != 1 || val("bSlope", 1) != 1 ||
                                    val("saturation", 1) != 1))
            s.exposure = "Non-equivariant";
        s.hdr = s.exposure == "Equivariant" ? "Scale-independent" : "Scale-dependent";
        s.invertibility = "Conditional exact";
        s.negative = "Native / signed-power extension";
        s.gamutDependence = "Colorimetric CAT/exposure; gamut-relative RGB/SOP";
    }
    if (e == Effect::Tone) {
        s.domain = "Look / Log";
        s.exposure = "Conditioned";
        if (val("contrast", 1) == 1 && val("toe", 0) == 0 && val("shoulder", 0) == 0 &&
            val("shadowDensity", 0) == 0 && val("highlightDensity", 0) == 0 && val("rContrast", 1) == 1 &&
            val("gContrast", 1) == 1 && val("bContrast", 1) == 1)
            s.exposure = "Equivariant";
        s.negative = "Selected encoder domain";
        s.neutralAxis = "Preserved with linked/equal per-channel settings";
        s.invertibility = "Monotonic scalar, approximate inverse; linked inverse not claimed";
    }
    if (e == Effect::Crosstalk) {
        s.domain = val("domain", 0) ? "Look / Log" : "Scene Linear";
        s.exposure = val("domain", 0) ? "Non-equivariant" : "Equivariant";
        s.hdr = val("domain", 0) ? "Scale-dependent" : "Scale-independent";
        s.invertibility = "Exact if effective matrix nonsingular";
        s.neutralAxis = val("mode", 1) == 1 || val("mode", 1) == 2 ? "Preserved" : "Not promised";
        s.neutralMagnitude = val("mode", 1) == 1 ? "Preserved" : "Not promised";
        s.negative = val("domain", 0) ? "Selected encoder domain" : "Native";
    }
    if (e == Effect::Volume || e == Effect::Crossover) {
        s.domain = "Perceptual / Opponent";
        s.negative = "Our real-cube-root signed extension";
        s.neutralAxis = "Protected continuously";
        s.gamutDependence = "Colorimetric; local matrices / channel crossover gamut-relative";
    }
    if (e == Effect::Density || e == Effect::Strip) {
        s.domain = "Spectral-derived";
        s.reference = "Scene-compatible radiance-base attenuation + signed residual";
        s.status = "Spectral basis research candidate; artist/host acceptance pending";
        s.negative = "Smooth positive emitted base + explicit signed XYZ residual";
        s.gamutDependence = "Colorimetric spectral basis; explicit custom record basis";
        s.neutralAxis = "Explicit anchor / distance protection";
    }
    if (e == Effect::Crossover && val("mode", 0) == 1) {
        s.domain = "Look / Log";
        s.negative = "Selected encoder domain";
        s.neutralAxis = "Only with equal channel trajectories";
        s.gamutDependence = "Gamut-relative RGB";
    }
    if (e == Effect::Strip) {
        s.exposure = "Equivariant";
        s.hdr = "Scale-independent";
    }
    if (e == Effect::Inspector) {
        s.domain = "Custom / diagnostic";
        s.reference = "Mode-dependent diagnostic, input mode scene-linear";
        s.exposure = val("mode", 0) == 0 ? "Equivariant" : "Non-equivariant";
        s.hdr = val("mode", 0) == 0 ? "Scale-independent" : "Scale-dependent";
        s.status = "Research diagnostic";
    }
    return s;
}
} // namespace rendition
