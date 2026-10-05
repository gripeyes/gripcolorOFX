// Descriptor page assignments remain identical to the accepted 0.32 source.
#include "rendition/ui_layout.hpp"
#include <cassert>
namespace reference032 {using namespace rendition;}
#define rendition reference032
#define uiPage acceptedUiPage
#define customCoordinate acceptedCustomCoordinate
#include "fixtures/presentation-0.32/ui_layout.hpp"
#undef customCoordinate
#undef uiPage
#undef rendition
int main() {
    using namespace rendition;
    for(int index=0;index<12;++index) {
        auto effect=static_cast<Effect>(index);
        for(const auto &d:parameters(effect))assert(uiPage(effect,d)==reference032::acceptedUiPage(effect,d));
    }
    auto empty=[](const std::string &,double fallback){return fallback;};
    assert(!presentationEnabled(Effect::Base,"rx",empty));
    assert(!presentationEnabled(Effect::Palette,"Crosstalk_mix",empty));
    double lo=0,hi=0;
    assert(presentationRange(Effect::Base,"toeStart",empty,lo,hi) && lo==-20 && hi==0);
}
