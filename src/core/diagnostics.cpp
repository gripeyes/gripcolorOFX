#include "rendition/diagnostics.hpp"
#include <algorithm>
#include <limits>
namespace rendition {
namespace {
Mat3 estimate(const Snapshot &s, Vec3 x, double step) {
    Mat3 j;
    for (int col = 0; col < 3; ++col) {
        Vec3 lo=x, hi=x;
        lo[col]-=float(step); hi[col]+=float(step);
        const double distance=double(hi[col])-double(lo[col]);
        if (!(distance>0)) throw std::domain_error("Jacobian step below float precision");
        Vec3 a=s.apply(lo), b=s.apply(hi);
        if (!finite(a) || !finite(b)) throw std::domain_error("Nonfinite Jacobian probe");
        for (int row=0;row<3;++row) j.v[row*3+col]=(double(b[row])-double(a[row]))/distance;
    }
    return j;
}
std::array<double,3> singularValues(const Mat3 &j) {
    double a[3][3]{};
    for(int r=0;r<3;++r) for(int c=0;c<3;++c) for(int k=0;k<3;++k)
        a[r][c]+=j.v[k*3+r]*j.v[k*3+c];
    // Symmetric Jacobi eigensolver for J^T J. No eigenvectors needed.
    for(int iteration=0;iteration<32;++iteration) {
        int p=0,q=1;
        for(int r=0;r<3;++r) for(int c=r+1;c<3;++c)
            if(std::abs(a[r][c])>std::abs(a[p][q])) {p=r;q=c;}
        double scale=std::max({std::abs(a[0][0]),std::abs(a[1][1]),std::abs(a[2][2]),1e-30});
        if(std::abs(a[p][q])<=1e-14*scale) break;
        double angle=.5*std::atan2(2*a[p][q],a[q][q]-a[p][p]);
        double c=std::cos(angle),s=std::sin(angle),app=a[p][p],aqq=a[q][q],apq=a[p][q];
        for(int k=0;k<3;++k) if(k!=p && k!=q) {
            double kp=a[k][p],kq=a[k][q];
            a[k][p]=a[p][k]=c*kp-s*kq;a[k][q]=a[q][k]=s*kp+c*kq;
        }
        a[p][p]=c*c*app-2*s*c*apq+s*s*aqq;
        a[q][q]=s*s*app+2*s*c*apq+c*c*aqq;a[p][q]=a[q][p]=0;
    }
    std::array<double,3> values{std::sqrt(std::max(0.,a[0][0])),std::sqrt(std::max(0.,a[1][1])),std::sqrt(std::max(0.,a[2][2]))};
    std::sort(values.begin(),values.end(),std::greater<double>());return values;
}
}
Differential differential(const Snapshot &s, Vec3 rgb, double relativeStep) {
    if(!finite(rgb) || !std::isfinite(relativeStep) || relativeStep<1e-6 || relativeStep>.1)
        throw std::invalid_argument("Invalid finite-difference input/step");
    Differential result{};
    if(s.isIdentity()) {
        result.jacobian=Mat3{};result.determinant=1;result.singularValues={1,1,1};
        result.condition=1;result.stepDisagreement=0;result.reliable=true;return result;
    }
    double step=relativeStep*std::max({double(std::abs(rgb.x)),double(std::abs(rgb.y)),double(std::abs(rgb.z)),.18});
    Mat3 coarse=estimate(s,rgb,step);result.jacobian=estimate(s,rgb,step*.5);
    double error=0,norm=0;
    for(int k=0;k<9;++k) {double delta=result.jacobian.v[k]-coarse.v[k];error+=delta*delta;norm+=result.jacobian.v[k]*result.jacobian.v[k];}
    result.stepDisagreement=std::sqrt(error)/std::max(std::sqrt(norm),1e-12);
    const auto &a=result.jacobian.v;
    result.determinant=a[0]*(a[4]*a[8]-a[5]*a[7])-a[1]*(a[3]*a[8]-a[5]*a[6])+a[2]*(a[3]*a[7]-a[4]*a[6]);
    result.singularValues=singularValues(result.jacobian);
    result.condition=result.singularValues[2]>1e-12 ? result.singularValues[0]/result.singularValues[2] : std::numeric_limits<double>::infinity();
    result.reliable=result.stepDisagreement<=.05;return result;
}
Vec3 differentialView(const Differential &d,int mode) {
    if(!d.reliable) return {1,0,1}; // unreliable step convergence: magenta
    if(d.determinant<=0) return {1,0,0}; // folding/collapse: red
    double value=0;
    if(mode==11) value=.5+.125*std::log2(std::max(d.determinant,1e-12));
    else if(mode==12) value=std::log2(std::max(d.condition,1.))/12;
    else if(mode==13) value=.5+.125*std::log2(std::max(d.singularValues[0],1e-12));
    else if(mode==14) value=.5+.125*std::log2(std::max(d.singularValues[2],1e-12));
    else value=d.stepDisagreement/.05;
    float v=float(std::clamp(value,0.,1.));return {v,v,v};
}
}
