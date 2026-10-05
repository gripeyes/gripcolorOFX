// Exercise the real shared OFX action dispatcher with a strict mock host.
#include "../src/ofx/plugin.cpp"
#include <cassert>
#include <cstdarg>
#include <condition_variable>
#include <functional>
struct MockProperties {
    Instance *instance = nullptr;
    double time = 1;
    float *pixels = nullptr;
    bool connected = true;
};
struct MockParam { std::string id; double value; bool choice; };
struct MockClip { MockProperties image; OfxStatus status = kOfxStatOK; bool malformed = false; };
struct Fixture {
    Instance instance;
    MockProperties effect, args, result, clipProps;
    std::map<std::string,MockParam> parameters;
    MockParam role{"hostSceneLinear",2,true};
    float input[4]{-.1f,.2f,4.f,.37f}, output[4]{};
    MockClip source, destination, reference;
    int untimed = 0, timed = 0, roleReads = 0, release = 0;
    bool animated = false, identity = false, aborted = false, missingOptional = false;
    int acquisitions = 0, renderAcquisitions = 0;
    bool requireOutputFirst = false;
    bool outputOwned = false;
    OfxStatus parameterStatus = kOfxStatOK;
    std::map<OfxPropertySetHandle,int> releasedHandles;
    std::function<void()> outputHook;
    std::function<void(MockClip&)> imageHook;
    int abortReads=0, abortAtRead=0, errors=0, clears=0;
    double requested = 1;
    explicit Fixture(Effect e) {
        instance.effect=e;instance.defs=parametersFor(e);
        for(auto &d:instance.defs) {
            auto &p=parameters[d.id];p={d.id,d.value,!d.choices.empty()};
            instance.params[d.id]=reinterpret_cast<OfxParamHandle>(&p);
        }
        effect.instance=&instance;
        source.image.pixels=input;destination.image.pixels=output;reference.image.pixels=input;
        instance.source=reinterpret_cast<OfxImageClipHandle>(&source);
        instance.output=reinterpret_cast<OfxImageClipHandle>(&destination);
        instance.reference=reinterpret_cast<OfxImageClipHandle>(&reference);
        instance.sourceProps=reinterpret_cast<OfxPropertySetHandle>(&clipProps);
        instance.referenceProps=reinterpret_cast<OfxPropertySetHandle>(&clipProps);
        instance.hostSceneLinear=reinterpret_cast<OfxParamHandle>(&role);
        if(e==Effect::Inspector)parameters["mode"].value=0;
    }
    static std::vector<Parameter> parametersFor(Effect e) { return rendition::parameters(e); }
};
thread_local Fixture *current;
OfxStatus getEffect(OfxImageEffectHandle, OfxPropertySetHandle *out) {
    *out=reinterpret_cast<OfxPropertySetHandle>(&current->effect);return kOfxStatOK;
}
OfxStatus getPointer(OfxPropertySetHandle h,const char *name,int,void **out) {
    auto &p=*reinterpret_cast<MockProperties*>(h);
    *out=std::string(name)==kOfxPropInstanceData?static_cast<void*>(p.instance):p.pixels;
    return kOfxStatOK;
}
OfxStatus getDouble(OfxPropertySetHandle h,const char *name,int,double *out) {
    *out=std::string(name)==kOfxPropTime?reinterpret_cast<MockProperties*>(h)->time:1.;return kOfxStatOK;
}
OfxStatus getDoubles(OfxPropertySetHandle,const char*,int n,double *out) {
    if(current->missingOptional)return kOfxStatErrUnknown;
    for(int j=0;j<n;j++)out[j]=1;return kOfxStatOK;
}
OfxStatus getInt(OfxPropertySetHandle h,const char *name,int,int *out) {
    if(current->missingOptional && (std::string(name)==kOfxImageEffectPropInteractiveRenderStatus || std::string(name)==kOfxImageEffectPropMetalEnabled))return kOfxStatErrUnknown;
    *out=std::string(name)==kOfxImagePropRowBytes?16:std::string(name)==kOfxImageClipPropConnected?reinterpret_cast<MockProperties*>(h)->connected:0;
    return kOfxStatOK;
}
OfxStatus getInts(OfxPropertySetHandle,const char*,int n,int *out) {
    assert(n==4);out[0]=out[1]=0;out[2]=out[3]=1;return kOfxStatOK;
}
OfxStatus getString(OfxPropertySetHandle,const char *name,int,char **out) {
    static char depth[]=kOfxBitDepthFloat,rgba[]=kOfxImageComponentRGBA,space[]="Linear Rec.2020",field[]=kOfxImageFieldNone;
    if(std::string(name)==kOfxImageEffectPropFieldToRender) {
        if(current->missingOptional)return kOfxStatErrUnknown;
        *out=field;return kOfxStatOK;
    }
    *out=std::string(name)==kOfxImageEffectPropPixelDepth?depth:std::string(name)==kOfxImageEffectPropComponents?rgba:space;return kOfxStatOK;
}
OfxStatus setString(OfxPropertySetHandle,const char*,int,const char*) {return kOfxStatOK;}
OfxStatus setDouble(OfxPropertySetHandle,const char*,int,double) {return kOfxStatOK;}
OfxStatus untimed(OfxParamHandle,...) {++current->untimed;return kOfxStatFailed;}
OfxStatus timed(OfxParamHandle h,double t,...) {
    assert(t==current->requested);++current->timed;
    if(current->requireOutputFirst && std::string(suiteTrace.action)==kOfxImageEffectActionRender)
        assert(current->outputOwned && current->renderAcquisitions==1);
    if(current->parameterStatus!=kOfxStatOK)return current->parameterStatus;
    auto &p=*reinterpret_cast<MockParam*>(h);double value=p.value;
    if(p.id=="hostSceneLinear") {++current->roleReads;if(current->animated)value=t==1?2:t==2?3:4;}
    if(current->animated && p.id=="interpretation")value=t==4?3:0;
    if(current->animated && p.id=="rx")value=p.value+.001*t;
    if(p.id=="exposure" && !current->identity)value=1;
    va_list a;va_start(a,t);
    if(p.choice)*va_arg(a,int*)=int(value);else *va_arg(a,double*)=value;
    va_end(a);return kOfxStatOK;
}
OfxStatus image(OfxImageClipHandle h,double t,const OfxRectD*,OfxPropertySetHandle *out) {
    assert(t==current->requested);auto &clip=*reinterpret_cast<MockClip*>(h);
    if(current->requireOutputFirst && current->renderAcquisitions==0)assert(&clip==&current->destination);
    ++current->renderAcquisitions;
    ++current->acquisitions;
    if(&clip==&current->destination && current->outputHook)current->outputHook();
    if(current->imageHook)current->imageHook(clip);
    if(clip.status!=kOfxStatOK)return clip.status;
    *out=reinterpret_cast<OfxPropertySetHandle>(&clip.image);
    if(&clip==&current->destination)current->outputOwned=true;
    if(clip.malformed)clip.image.pixels=nullptr;
    return kOfxStatOK;
}
OfxStatus release(OfxPropertySetHandle h) {
    if(h==reinterpret_cast<OfxPropertySetHandle>(&current->destination.image)) {assert(current->outputOwned);current->outputOwned=false;}
    ++current->release;++current->releasedHandles[h];return kOfxStatOK;}
OfxStatus rod(OfxImageClipHandle,double,OfxRectD *out) {*out={0,0,1,1};return kOfxStatOK;}
int abortRender(OfxImageEffectHandle) {
    if(++current->abortReads==current->abortAtRead)current->aborted=true;
    return current->aborted;
}
OfxStatus persistent(void*,const char *type,const char*,const char*,...) {
    if(std::string(type)==kOfxMessageError)++current->errors;return kOfxStatOK;
}
OfxStatus clearMessage(void*) {++current->clears;return kOfxStatOK;}
OfxStatus run(Fixture &f,const char *a,double time=1) {
    current=&f;f.requested=f.args.time=time;
    if(std::string(a)==kOfxImageEffectActionRender)f.renderAcquisitions=0;
    return action(f.instance.effect,a,reinterpret_cast<OfxImageEffectHandle>(&f),reinterpret_cast<OfxPropertySetHandle>(&f.args),reinterpret_cast<OfxPropertySetHandle>(&f.result));
}
int main() {
    OfxImageEffectSuiteV1 effectSuite{};effectSuite.getPropertySet=getEffect;effectSuite.clipGetImage=image;effectSuite.clipReleaseImage=release;effectSuite.clipGetRegionOfDefinition=rod;effectSuite.abort=abortRender;fx=&effectSuite;
    OfxPropertySuiteV1 propertySuite{};propertySuite.propGetPointer=getPointer;propertySuite.propGetDouble=getDouble;propertySuite.propGetDoubleN=getDoubles;propertySuite.propGetInt=getInt;propertySuite.propGetIntN=getInts;propertySuite.propGetString=getString;propertySuite.propSetString=setString;propertySuite.propSetDouble=setDouble;prop=&propertySuite;
    OfxParameterSuiteV1 parameterSuite{};parameterSuite.paramGetValue=untimed;parameterSuite.paramGetValueAtTime=timed;param=&parameterSuite;
    OfxMessageSuiteV2 messageSuite{};messageSuite.setPersistentMessage=persistent;messageSuite.clearPersistentMessage=clearMessage;msg=&messageSuite;
    // Render and IsIdentity evaluate all 12 registered effects with no current-value reads.
    for(int e=0;e<12;e++) {
        Fixture f(static_cast<Effect>(e));f.requireOutputFirst=true;assert(run(f,kOfxImageEffectActionRender)==kOfxStatOK);
        assert(f.untimed==0 && f.timed>0 && f.roleReads==1);
        assert(f.output[3]==f.input[3]);
        if(e==int(Effect::Base) || e==int(Effect::Scene))assert(std::abs(f.output[2]-8)<1e-5);
        f.identity=true;assert(run(f,kOfxImageEffectActionIsIdentity)==kOfxStatOK);
        assert(f.untimed==0 && f.roleReads==2);
        f.source.status=kOfxStatFailed;
        assert(run(f,kOfxImageEffectActionRender)==kOfxStatOK);
        for(float v:f.output)assert(v==0); // absent connected Source is transparent black
        f.source.status=kOfxStatErrBadHandle;
        assert(run(f,kOfxImageEffectActionRender)==kOfxStatFailed);
        f.source.status=kOfxStatErrMemory;
        assert(run(f,kOfxImageEffectActionRender)==kOfxStatFailed);
        f.source.status=kOfxStatOK;f.destination.status=kOfxStatFailed;
        assert(run(f,kOfxImageEffectActionRender)==kOfxStatFailed);
        f.destination.status=kOfxStatOK;f.source.malformed=true;
        assert(run(f,kOfxImageEffectActionRender)==kOfxStatFailed);
    }
    // Output is owned before snapshot evaluation; a snapshot failure unwinds it once.
    for(int e=0;e<12;++e) {
        Fixture invalid(static_cast<Effect>(e));invalid.requireOutputFirst=true;
        invalid.parameterStatus=kOfxStatErrBadHandle;
        assert(run(invalid,kOfxImageEffectActionRender)==kOfxStatFailed);
        assert(invalid.acquisitions==1 && invalid.release==1 && invalid.errors==1);
        assert(invalid.releasedHandles[reinterpret_cast<OfxPropertySetHandle>(&invalid.destination.image)]==1);
    }
    Fixture animated(Effect::Base);animated.animated=true;
    for(double time:{1.,2.,3.,4.}) {
        assert(run(animated,kOfxImageEffectActionRender,time)==kOfxStatOK);
        animated.identity=true;
        assert(run(animated,kOfxImageEffectActionIsIdentity,time)==kOfxStatOK);
        animated.identity=false;
    }
    assert(animated.untimed==0 && animated.roleReads==6);
    // Missing optional Matte participates with zero coverage, never full-image dodge.
    Fixture matte(Effect::Base);matte.identity=true;matte.parameters["localExposure"].value=1;matte.reference.status=kOfxStatFailed;
    assert(run(matte,kOfxImageEffectActionRender)==kOfxStatOK);
    for(int c=0;c<4;c++)assert(std::abs(matte.output[c]-matte.input[c])<2e-6f+2e-5f*std::abs(matte.input[c]));
    // Cancellation is internal control flow; genuine Output failures remain fatal.
    using namespace rendition::ofx_trace;
    setenv("RENDITION_SUITE_TRACE","1",1);
    Fixture missing(Effect::Base);missing.missingOptional=true;
    assert(run(missing,kOfxImageEffectActionRender)==kOfxStatOK);
    auto events=snapshot();bool missingRecorded=false;
    for(size_t n=0;n<events.size;++n) {
        const auto &e=events.events[n];
        if(e.instance==&missing && std::string(e.stage)=="render-entry") {
            missingRecorded=e.propertyStatus[1]!=kOfxStatOK && e.propertyStatus[2]!=kOfxStatOK &&
                e.interactive==-1 && e.gpu==-1 && e.time==1;
        }
    }
    assert(missingRecorded);
    // Read-only diagnostics are output-identical for artist and historical paths.
    for(auto effect:{Effect::Base,Effect::Palette,Effect::Material,Effect::Scene}) {
        unsetenv("RENDITION_SUITE_TRACE");Fixture plain(effect);
        assert(run(plain,kOfxImageEffectActionRender)==kOfxStatOK);
        setenv("RENDITION_SUITE_TRACE","1",1);Fixture traced(effect);
        assert(run(traced,kOfxImageEffectActionRender)==kOfxStatOK);
        assert(std::memcmp(plain.output,traced.output,sizeof(plain.output))==0);
    }
    // All shared entry paths: pre-abort does no acquisition; failed fetch + abort is clean.
    for(int e=0;e<12;++e) {
        Fixture pre(static_cast<Effect>(e));pre.aborted=true;
        assert(run(pre,kOfxImageEffectActionRender)==kOfxStatOK);
        assert(pre.acquisitions==0 && pre.release==0 && pre.errors==0 && pre.clears==0);
        Fixture failure(static_cast<Effect>(e));failure.destination.status=kOfxStatFailed;
        assert(run(failure,kOfxImageEffectActionRender)==kOfxStatFailed);
        assert(failure.errors==1 && failure.release==0);
        events=snapshot();const auto &fetch=events.events[events.size-2];
        assert(fetch.fetchStatus==kOfxStatFailed && fetch.abortBefore==0 && fetch.abortAfter==0);
        // Cancellation arrives while host is acquiring Output.
        failure.outputHook=[&]{failure.aborted=true;};
        for(int repeat=0;repeat<3;++repeat) {
            failure.aborted=false;
            assert(run(failure,kOfxImageEffectActionRender)==kOfxStatOK);
            assert(failure.errors==1 && failure.release==0);
            events=snapshot();bool caught=false;
            for(size_t n=0;n<events.size;++n) {
                const auto &event=events.events[n];
                if(event.renderId==events.events[events.size-1].renderId && std::string(event.stage)=="acquire-result")
                    caught=event.abortBefore==0 && event.abortAfter==1 && event.fetchStatus==kOfxStatFailed;
            }
            assert(caught && std::string(events.events[events.size-1].stage)=="render-exit-cancelled");
        }
        failure.destination.status=kOfxStatOK;failure.outputHook={};failure.aborted=false;
        assert(run(failure,kOfxImageEffectActionRender)==kOfxStatOK);
        assert(failure.release==2);
        // Successful acquisition followed by abort releases the new handle only.
        Fixture acquired(static_cast<Effect>(e));acquired.outputHook=[&]{acquired.aborted=true;};
        assert(run(acquired,kOfxImageEffectActionRender)==kOfxStatOK);
        assert(acquired.acquisitions==1 && acquired.release==1 && acquired.errors==0 && acquired.clears==0);
        // Cancellation detected by pixel-loop polling releases both images, no messages.
        Fixture processing(static_cast<Effect>(e));processing.abortAtRead=6;
        assert(run(processing,kOfxImageEffectActionRender)==kOfxStatOK);
        assert(processing.release==2 && processing.errors==0 && processing.clears==0);
    }
    // Failed Source, Reference and Matte acquisition also distinguish cancellation.
    for(int role=0;role<3;++role) {
        Fixture input(role==1?Effect::Inspector:Effect::Base);
        if(role==1)input.parameters["mode"].value=8;
        if(role==2)input.parameters["localExposure"].value=1;
        auto &clip=role==0?input.source:input.reference;
        clip.status=kOfxStatFailed;
        input.imageHook=[&](MockClip &fetched){if(&fetched==&clip)input.aborted=true;};
        assert(run(input,kOfxImageEffectActionRender)==kOfxStatOK);
        assert(input.release==(role==0?1:2) && input.errors==0 && input.clears==0);
    }
    // Bad handles/memory failures cannot be hidden merely because abort became true.
    for(auto status:{kOfxStatErrBadHandle,kOfxStatErrMemory}) {
        Fixture fatal(Effect::Base);fatal.destination.status=status;
        fatal.outputHook=[&]{fatal.aborted=true;};
        assert(run(fatal,kOfxImageEffectActionRender)==kOfxStatFailed);
        assert(fatal.errors==1 && fatal.release==0);
    }
    // Malformed acquired image releases Output plus the failing Source exactly once.
    Fixture malformed(Effect::Base);malformed.source.malformed=true;
    assert(run(malformed,kOfxImageEffectActionRender)==kOfxStatFailed);
    assert(malformed.release==2);
    assert(malformed.releasedHandles.size()==2);
    for(const auto &released:malformed.releasedHandles)assert(released.second==1);
    // Two actual dispatcher calls overlap: trace locking must not serialize fetches.
    Fixture parallel(Effect::Base);
    std::mutex barrierMutex;std::condition_variable barrier;int arrived=0;
    parallel.outputHook=[&]{
        std::unique_lock<std::mutex> lock(barrierMutex);
        ++arrived;barrier.notify_all();
        assert(barrier.wait_for(lock,std::chrono::seconds(5),[&]{return arrived==2;}));
    };
    // Share the instance identity but use thread-local mock fixtures/storage/counters.
    Fixture parallelOther(Effect::Base);parallelOther.outputHook=parallel.outputHook;
    auto runParallel=[&](Fixture &f) {
        ::current=&f;f.requested=f.args.time=1;
        assert(action(Effect::Base,kOfxImageEffectActionRender,
            reinterpret_cast<OfxImageEffectHandle>(&parallel),
            reinterpret_cast<OfxPropertySetHandle>(&f.args),
            reinterpret_cast<OfxPropertySetHandle>(&f.result))==kOfxStatOK);
    };
    const auto beforeParallel=snapshot();
    const auto parallelStart=beforeParallel.events[beforeParallel.size-1].sequence;
    std::thread first([&]{runParallel(parallel);}), second([&]{runParallel(parallelOther);});
    first.join();second.join();
    assert(parallel.release==2 && parallelOther.release==2);
    events=snapshot();bool overlap=false;std::map<uint64_t,size_t> renderThreads;
    for(size_t n=0;n<events.size;++n) {
        const auto &event=events.events[n];
        if(event.instance==&parallel && event.sequence>parallelStart) {
            overlap|=event.active==2;
            renderThreads[event.renderId]=event.thread;
        }
    }
    assert(overlap && renderThreads.size()==2 && renderThreads.begin()->second!=renderThreads.rbegin()->second);
    {std::lock_guard<std::mutex> lock(state.mutex);assert(state.active.empty());}
    // A successful render storm retains only the newest fixed-capacity events.
    Fixture history(Effect::Base);
    for(int n=0;n<100;++n)assert(run(history,kOfxImageEffectActionRender)==kOfxStatOK);
    events=snapshot();assert(events.size==historyCapacity);
    for(size_t n=1;n<events.size;++n)assert(events.events[n].sequence>events.events[n-1].sequence);
    const auto finalId=events.events[events.size-1].renderId;
    unsetenv("RENDITION_SUITE_TRACE");
    assert(run(history,kOfxImageEffectActionRender)==kOfxStatOK);
    assert(snapshot().events[historyCapacity-1].renderId==finalId && rendition::ofx_trace::current==nullptr);
    std::puts("Correlated render diagnostics: optional properties, cancellation semantics, RAII, shared effects, concurrency and bounded history passed; not Nuke acceptance");
    std::puts("OFX runtime compliance: timed Render/Identity, animated configuration, unavailable inputs, fatal output/image failures passed");
}
