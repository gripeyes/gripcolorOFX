#include "rendition/primaries.hpp"
#include "rendition/kernel_math.hpp"
namespace rendition {
std::vector<Parameter> primariesParameters() {
    std::vector<Parameter> p;
    auto add=[&](const char* id,const char* label,double value,double lo,double hi,const char* group,const char* unit) {
        p.push_back({id,label,group,unit,value,lo,hi,{}});
    };
    add("exposure","Exposure",0,-20,20,"MASTER","stops");
    add("contrast","Contrast",1,.1,4,"MASTER","factor");
    add("pivot","Contrast pivot",0,-12,12,"MASTER","stops relative to 0.18");
    add("saturation","Saturation",1,0,4,"MASTER","factor");
    add("colourBalance","Density / colourfulness balance",0,-2,2,"MASTER","artistic stops; not spectral density");
    add("blackLevel","Black level",0,-.05,.05,"BLACK / TOE","scene Y offset at full shadow weight");
    add("toeStart","Toe start",-4,-20,4,"BLACK / TOE","stops relative to 0.18");
    add("toeSoftness","Toe softness",1,.25,8,"BLACK / TOE","stops");
    add("shadowCompression","Shadow compression",0,0,1,"BLACK / TOE","fraction; slope contribution 0 to 0.45");
    add("shadowHue","Shadow hue",240,0,360,"BLACK / TOE","degrees; RGB artist hue circle");
    add("shadowTint","Shadow tint",0,-1,1,"BLACK / TOE","dimensionless Y-preserving colour amount");
    add("shadowRetention","Shadow chroma retention",1,0,2,"BLACK / TOE","factor");
    add("colourDeath","Colour death",0,0,1,"BLACK / TOE","fraction");
    add("deathStart","Colour-death start",-6,-24,4,"BLACK / TOE","stops relative to 0.18");
    add("deathSoftness","Colour-death softness",2,.25,8,"BLACK / TOE","stops");
    add("midBalance","Midtone balance: cool / warm",0,-1,1,"MIDTONES","dimensionless Y-preserving colour amount");
    add("midExposure","Midtone exposure",0,-4,4,"MIDTONES","stops");
    add("midTint","Midtone tint: magenta / green",0,-1,1,"MIDTONES","dimensionless Y-preserving colour amount");
    add("midDensity","Midtone density",0,-2,2,"MIDTONES","stops of attenuation");
    add("midChroma","Midtone chroma",1,0,3,"MIDTONES","factor");
    add("whiteLevel","White level",0,-4,4,"WHITE / SHOULDER","stops at full highlight weight; no white cap");
    add("shoulderStart","Shoulder start",4,-4,20,"WHITE / SHOULDER","stops relative to 0.18");
    add("shoulderSoftness","Shoulder softness",1,.25,8,"WHITE / SHOULDER","stops");
    add("highlightCompression","Highlight compression",0,0,1,"WHITE / SHOULDER","fraction; slope contribution 0 to 0.45");
    add("highlightHue","Highlight hue",60,0,360,"WHITE / SHOULDER","degrees; RGB artist hue circle");
    add("highlightTint","Highlight tint",0,-1,1,"WHITE / SHOULDER","dimensionless Y-preserving colour amount");
    add("highlightRetention","Highlight chroma retention",1,0,2,"WHITE / SHOULDER","factor");
    add("highlightBleach","Highlight bleaching",0,0,1,"WHITE / SHOULDER","fraction; source chroma only, before tint");
    add("brillianceReduction","Brilliance reduction",0,0,2,"WHITE / SHOULDER","stops weighted by highlight colourfulness");
    add("shadowRange","Shadow range center",-3,-20,4,"RANGE","stops relative to 0.18");
    add("shadowSoftness","Shadow range softness",1,.25,8,"RANGE","stops");
    add("highlightRange","Highlight range center",3,-4,20,"RANGE","stops relative to 0.18");
    add("highlightSoftness","Highlight range softness",1,.25,8,"RANGE","stops");
    return p;
}
double PrimariesModel::get(const char *key) const { return v.at(key); }
PrimariesModel::PrimariesModel(const Snapshot &s, const Values &overrideValues, bool mono):v(overrideValues.empty()?s.parameterValues():overrideValues),monotonic(mono) {
    toReference=s.toReferenceWhite()*s.colorSpace().toXYZ;
    fromReference=s.colorSpace().fromXYZ*s.fromReferenceWhite();
    auto reference=ColorSpace::make(Gamut::Rec2020);
    artistToXYZ=reference.toXYZ;
    white=reference.toXYZ*Vec3{1,1,1};
    auto project=[&](Vec3 q) { return q-white*q.y; };
    warmAxis=project(reference.toXYZ*Vec3{1,0,-1});
    greenAxis=project(reference.toXYZ*Vec3{-.5f,1,-.5f});
    auto hueVector=[&](double hue) {
        // Continuous RGB artist hue circle. Project into the same zero-Y plane.
        double turn=hue/60.;Vec3 q;
        auto channel=[&](double offset) {double t=std::fmod(turn+offset,6.);return float(std::clamp(std::abs(t-3.)-1.,0.,1.));};
        q={channel(0),channel(4),channel(2)};
        // Reference primaries are fixed; source gamut never chooses a creative algorithm.
        auto mat=artistToXYZ;
        Vec3 ray=mat*q;return ray-white*ray.y;
    };
    shadowAxis=hueVector(get("shadowHue"));highlightAxis=hueVector(get("highlightHue"));
    if(monotonic) {
        // Integrate a positive derivative in stop coordinates, anchored at Pivot.
        // No output clamp and no hidden reduction of the parameter range.
        auto desired=[&](double e,double q) {
            double a=rendition_kernel::sigmoid(float((get("shadowRange")-e)/get("shadowSoftness")));
            double b=rendition_kernel::sigmoid(float((e-get("highlightRange"))/get("highlightSoftness")));
            double m=(1-a)*(1-b),total=a+b+m;a/=total;b/=total;m/=total;
            auto tail=[&](double z) {return .45*get("shadowCompression")*get("toeSoftness")*rendition_kernel::softplus(float((get("toeStart")-z)/get("toeSoftness"))) -.45*get("highlightCompression")*get("shoulderSoftness")*rendition_kernel::softplus(float((z-get("shoulderStart"))/get("shoulderSoftness")));};
            return get("pivot")+get("contrast")*(e-get("pivot")+tail(e)-tail(get("pivot"))) +m*(get("midExposure")-get("midDensity"))+b*get("whiteLevel")+a*get("blackStops")-q*(get("colourBalance")+b*get("brillianceReduction"));
        };
        auto slope=[&](double e,double q) {
            double d=(desired(e+.01,q)-desired(e-.01,q))/.02;
            // C1 positive rectifier: preserve slopes >= .1 exactly.
            return d>=.1?d: .000001+.099999*std::exp((d-.1)/.099999);
        };
        for(int q=0;q<=1;++q) {
          auto &map=q?colourToneMap:toneMap;map.resize(16385);map[0]=0;
          for(size_t i=1;i<map.size();++i)map[i]=map[i-1]+slope(-64+(double(i)-.5)/128,q)/128;
          double anchor=mappedTone(get("pivot"),q!=0);
          for(auto &x:map)x+=desired(get("pivot"),q)-anchor;
        }
    }

}
double PrimariesModel::mappedTone(double e,bool colourful) const {
    const auto &map=colourful?colourToneMap:toneMap;
    double z=(e+64)*128;
    if(z<=0)return map[0]+z*(map[1]-map[0]);
    if(z>=16384)return map.back()+(z-16384)*(map.back()-map[16383]);
    size_t i=size_t(z);return map[i]+(z-i)*(map[i+1]-map[i]);
}
Vec3 PrimariesModel::apply(Vec3 rgb) const {
    if(!finite(rgb)) throw std::domain_error("Nonfinite source RGB: use Inspector NaN / Inf mode");
    const double epsilon=.18*std::exp2(-20.);
    Vec3 xyz=toReference*rgb;
    double y=xyz.y*std::exp2(get("exposure"));
    Vec3 residual=(xyz-white*xyz.y)*float(std::exp2(get("exposure")));
    // Soft signed-magnitude coordinate: accurate stop interpretation above the explicit floor.
    double e=std::log2((std::abs(y)+epsilon)/.18);
    double s=rendition_kernel::sigmoid(float((get("shadowRange")-e)/get("shadowSoftness")));
    double h=rendition_kernel::sigmoid(float((e-get("highlightRange"))/get("highlightSoftness")));
    double m=(1-s)*(1-h),total=s+h+m;s/=total;h/=total;m/=total;
    auto tail=[&](double z) {
        return .45*get("shadowCompression")*get("toeSoftness")*rendition_kernel::softplus(float((get("toeStart")-z)/get("toeSoftness")))
             -.45*get("highlightCompression")*get("shoulderSoftness")*rendition_kernel::softplus(float((z-get("shoulderStart"))/get("shoulderSoftness")));
    };
    double pivot=.18*std::exp2(get("pivot"));
    double scale=std::pow((std::abs(y)+epsilon)/(pivot+epsilon),get("contrast")-1);
    scale*=std::exp2(get("contrast")*(tail(e)-tail(get("pivot"))) + m*(get("midExposure")-get("midDensity"))+h*get("whiteLevel"));
    double c=std::sqrt(double(residual.x)*residual.x+double(residual.z)*residual.z);
    double colourful=monotonic?(c==0 && y==0?0:c/std::sqrt(c*c+y*y)):c/std::sqrt(c*c+y*y+epsilon*epsilon);
    if(monotonic)scale=std::exp2((1-colourful)*mappedTone(e)+colourful*mappedTone(e,true)-e);
    else scale*=std::exp2(-colourful*(get("colourBalance")+h*get("brillianceReduction")));
    double shapedY=y*scale+get("blackLevel")*s;
    double chroma=get("saturation")*std::exp2(.25*get("colourBalance")*colourful);
    chroma*=s*get("shadowRetention")+m*get("midChroma")+h*get("highlightRetention");
    chroma*=1-h*get("highlightBleach");
    Vec3 coloured=residual*float(scale*chroma);
    Vec3 tint=shadowAxis*float(s*get("shadowTint"))
             +highlightAxis*float(h*get("highlightTint"))
             +(warmAxis*float(get("midBalance"))+greenAxis*float(get("midTint")))*float(m);
    coloured=coloured+tint*float(.3*std::abs(shapedY));
    double death=1-get("colourDeath")*rendition_kernel::sigmoid(float((get("deathStart")-e)/get("deathSoftness")));
    coloured=coloured*float(death);
    // Projection also removes floating-point leakage from source chroma/tint.
    coloured=coloured-white*coloured.y;
    return fromReference*(white*float(shapedY)+coloured);
}
}
