// Focused fault injection for diagnostics only; does not emulate Nuke behavior.
#include "../src/ofx/plugin.cpp"
#include <cassert>
#include <cstdarg>
OfxStatus roleStatus = kOfxStatOK;
OfxStatus mockRole(OfxParamHandle, double, ...) {
    return roleStatus;
}
OfxStatus unavailableImage(OfxImageClipHandle, OfxTime, const OfxRectD *, OfxPropertySetHandle *) {
    return kOfxStatFailed;
}
int main() {
    OfxParameterSuiteV1 parameters{};
    parameters.paramGetValueAtTime = mockRole;
    param = &parameters;
    OfxImageEffectSuiteV1 effects{};
    effects.clipGetImage = unavailableImage;
    fx = &effects;
    Instance i;
    int handleStorage = 0;
    i.hostSceneLinear = reinterpret_cast<OfxParamHandle>(&handleStorage);
    SuiteTraceAction outer(Effect::Base, kOfxImageEffectActionRender, &i);
    SuiteTraceSubject time("render", 42);
    // Successful checked calls must stay silent, with their existing behavior.
    checked(kOfxStatOK);
    roleStatus = kOfxStatFailed;
    try {
        interpretationRole(i, {{"interpretation", 0}}, 42);
        assert(false);
    } catch (const std::runtime_error &e) {
        assert(std::string(e.what()) == "OFX suite operation failed: 1");
    }
    assert(suiteTrace.depth == 1 && std::string(suiteTrace.subject) == "render");
    {
        SuiteTraceAction inner(Effect::Palette, kOfxImageEffectActionRender, &i);
        try {
            Image missing(nullptr, 84, ImageAccess::Output, false, "Output");
            assert(false);
        } catch (const std::runtime_error &e) {
            assert(std::string(e.what()) == "OFX suite operation failed: 1");
        }
        assert(suiteTrace.depth == 2 && std::string(suiteTrace.subject) == "none");
    }
    assert(suiteTrace.depth == 1 && suiteTrace.effect == int(Effect::Base));
    assert(suiteTrace.timed && suiteTrace.time == 42);
    std::puts("suite trace fault injection passed; not a Nuke reproduction");
}
