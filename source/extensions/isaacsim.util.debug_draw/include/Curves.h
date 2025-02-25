// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <iostream>

namespace isaacsim
{
namespace util
{
namespace debug_draw
{
namespace curves
{

/**
 * @brief Enumeration of supported basis curve types
 */
enum class eBasisCurveType
{
    /**
     * @brief Bezier curve type using Bernstein polynomials
     */
    Bezier = 0,

    /**
     * @brief Catmull-Rom spline curve type
     */
    CatmullRom = 1,

    /**
     * @brief B-spline curve type
     */
    BSpline = 2
};

/**
 * @brief Enumeration of curve wrapping modes
 */
enum class eBasisCurveWrap
{
    /**
     * @brief Curve wraps around to form a closed loop
     */
    Periodic = 0,

    /**
     * @brief Curve has distinct start and end points
     */
    NonPeriodic = 1,

    /**
     * @brief Curve is pinned at endpoints with special handling
     */
    Pinned = 2
};

/**
 * @brief Coefficients for spline curve basis functions and their tangents
 * @details Contains the basis function coefficients and tangent basis coefficients
 *          used in spline curve calculations
 */
struct coeff
{
    /**
     * @brief Basis function coefficients for curve position calculation
     */
    pxr::GfVec4f basis;

    /**
     * @brief Basis function coefficients for curve tangent calculation
     */
    pxr::GfVec4f tangentBasis;
};

/**
 * @brief Base class for all spline-based curves
 * @details Provides common functionality for different types of spline curves,
 *          including tessellation, evaluation, and segment handling
 */
class SplineCurve
{

public:
    /**
     * @brief Step size for curve tessellation
     * @details Controls the density of points generated during curve tessellation.
     *          Smaller values create smoother curves with more points.
     */
    float m_stepSize = 0.1f;

    /**
     * @brief Constructs a SplineCurve with specified wrap mode and vertex step
     * @param[in] wrapMode The wrapping behavior of the curve
     * @param[in] vstep Number of control points to step between curve segments
     */
    SplineCurve(eBasisCurveWrap wrapMode, uint32_t vstep) : m_wrapMode(wrapMode), m_vstep(vstep)
    {
    }
    virtual ~SplineCurve() = default;

    /**
     * @brief Tessellates the curve into a series of points and tangents
     * @details Converts control points into a series of tessellated points and their
     *          corresponding tangents based on the curve's mathematical properties
     *
     * @param[in] controlPoints Array of control points defining the curve
     * @param[out] tessellatedPoints Output array of tessellated points
     * @param[out] tessellatedTangents Output array of tangent vectors at tessellated points
     */
    virtual void tessellate(const pxr::VtArray<pxr::GfVec3f>& controlPoints,
                            pxr::VtArray<pxr::GfVec4f>& tessellatedPoints,
                            pxr::VtArray<pxr::GfVec4f>& tessellatedTangents)
    {
        size_t numControlPoints = controlPoints.size();

        // return straight line
        if (numControlPoints < 3)
        {
            pxr::GfVec3f cp0 = controlPoints[0];
            pxr::GfVec4f p0 = pxr::GfVec4f(cp0[0], cp0[1], cp0[2], 1);
            pxr::GfVec3f cp1 = controlPoints[0];
            pxr::GfVec4f p1 = pxr::GfVec4f(cp1[0], cp1[1], cp1[2], 1);
            pxr::GfVec4f t = p1 - p0;
            tessellatedPoints.push_back(p0);
            tessellatedPoints.push_back(p1);
            tessellatedTangents.push_back(t);
            tessellatedTangents.push_back(t);
            return;
        }

        size_t curveSegments = (numControlPoints - 4) / m_vstep + 1;

        if (m_wrapMode == eBasisCurveWrap::Pinned)
        {
            injectTessellatedSegment(controlPoints, tessellatedPoints, tessellatedTangents, 0);
        }

        size_t controlPointIndex = 0;
        for (size_t i = 0; i < curveSegments; ++i)
        {
            eval(controlPoints, tessellatedPoints, tessellatedTangents, controlPointIndex);
            controlPointIndex += m_vstep;
        }

        if (m_wrapMode == eBasisCurveWrap::Pinned)
        {
            injectTessellatedSegment(controlPoints, tessellatedPoints, tessellatedTangents, numControlPoints);
        }
    }

protected:
    /**
     * @brief Evaluates the basis functions for the curve
     * @details Calculates the coefficients for both position and tangent at a given parameter value
     *
     * @param[in] u The parameter value (1-t)
     * @param[in] u2 The square of the parameter value (u^2)
     * @param[in] u3 The cube of the parameter value (u^3)
     * @return Coefficients for curve position and tangent calculation
     */
    virtual coeff evalBasis(float u, float u2, float u3) = 0;

    /**
     * @brief Evaluates a segment of the curve
     * @details Computes tessellated points and tangents for a curve segment
     *          defined by four control points
     *
     * @param[in] controlPoints Array of all control points
     * @param[out] tessellatedPoints Output array for computed points
     * @param[out] tessellatedTangents Output array for computed tangents
     * @param[in] index Starting index in control points array for this segment
     */
    virtual void eval(const pxr::VtArray<pxr::GfVec3f>& controlPoints,
                      pxr::VtArray<pxr::GfVec4f>& tessellatedPoints,
                      pxr::VtArray<pxr::GfVec4f>& tessellatedTangents,
                      size_t index)
    {
        pxr::GfVec3f cp = controlPoints[index];
        pxr::GfVec4f p0 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
        cp = controlPoints[index + 1];
        pxr::GfVec4f p1 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
        cp = controlPoints[index + 2];
        pxr::GfVec4f p2 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
        cp = controlPoints[index + 3];
        pxr::GfVec4f p3 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);

        float t = 0.0;
        float tStep = m_stepSize;
        while (t < 1.0)
        {
            float u = 1.0f - t;
            coeff cf = evalBasis(u, u * u, u * u * u);
            t += tStep;
            tessellatedPoints.push_back(
                static_cast<pxr::GfVec4f>(p0 * cf.basis[0] + p1 * cf.basis[1] + p2 * cf.basis[2] + p3 * cf.basis[3]));
            tessellatedTangents.push_back(static_cast<pxr::GfVec4f>(p0 * cf.tangentBasis[0] + p1 * cf.tangentBasis[1] +
                                                                    p2 * cf.tangentBasis[2] + p3 * cf.tangentBasis[3]));
        }
    }

    /**
     * @brief Injects additional tessellated segments for curve endpoints
     * @details Handles special cases for curve endpoints when using pinned wrap mode
     *
     * @param[in] controlPoints Array of all control points
     * @param[out] tessellatedPoints Output array for computed points
     * @param[out] tessellatedTangents Output array for computed tangents
     * @param[in] index Index indicating which endpoint (0 for start, size for end)
     */
    virtual void injectTessellatedSegment(const pxr::VtArray<pxr::GfVec3f>& controlPoints,
                                          pxr::VtArray<pxr::GfVec4f>& tessellatedPoints,
                                          pxr::VtArray<pxr::GfVec4f>& tessellatedTangents,
                                          size_t index)
    {
        pxr::GfVec4f p0;
        pxr::GfVec4f p1;
        pxr::GfVec4f p2;
        pxr::GfVec4f p3;
        if (index == 0)
        {
            pxr::GfVec3f cp0 = controlPoints[index];
            pxr::GfVec3f cp1 = controlPoints[index + 1];
            pxr::GfVec4f gfCp0 = pxr::GfVec4f(cp0[0], cp0[1], cp0[2], 1);
            pxr::GfVec4f gfCp1 = pxr::GfVec4f(cp1[0], cp1[1], cp1[2], 1);
            p0 = 2 * gfCp0 - gfCp1;
            pxr::GfVec3f cp = controlPoints[index];
            p1 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
            cp = controlPoints[index + 1];
            p2 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
            cp = controlPoints[index + 2];
            p3 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
        }
        else
        {
            pxr::GfVec3f cp1 = controlPoints[index - 1];
            pxr::GfVec3f cp2 = controlPoints[index - 2];
            pxr::GfVec4f gfCp1 = pxr::GfVec4f(cp1[0], cp1[1], cp1[2], 1);
            pxr::GfVec4f gfCp2 = pxr::GfVec4f(cp2[0], cp2[1], cp2[2], 1);
            pxr::GfVec3f cp = controlPoints[index - 3];
            p0 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
            cp = controlPoints[index - 2];
            p1 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
            cp = controlPoints[index - 1];
            p2 = pxr::GfVec4f(cp[0], cp[1], cp[2], 1);
            p3 = 2 * gfCp1 - gfCp2;
        }

        float t = 0.0;
        float tStep = m_stepSize;
        while (t < 1.0)
        {
            float u = 1.0f - t;
            coeff cf = evalBasis(u, u * u, u * u * u);
            t += tStep;
            tessellatedPoints.push_back(
                static_cast<pxr::GfVec4f>(p0 * cf.basis[0] + p1 * cf.basis[1] + p2 * cf.basis[2] + p3 * cf.basis[3]));
            tessellatedTangents.push_back(static_cast<pxr::GfVec4f>(p0 * cf.tangentBasis[0] + p1 * cf.tangentBasis[1] +
                                                                    p2 * cf.tangentBasis[2] + p3 * cf.tangentBasis[3]));
        }
    }

    /**
     * @brief The wrapping behavior of the curve
     */
    eBasisCurveWrap m_wrapMode;

    /**
     * @brief Number of control points to step between curve segments
     */
    uint32_t m_vstep;
};

/**
 * @brief Catmull-Rom spline curve implementation
 * @details A type of cubic spline that passes through its control points and
 *          provides C1 continuity. Commonly used for smooth interpolation
 *          between keyframes or points.
 */
class CatmullRom : public SplineCurve
{
public:
    /**
     * @brief Constructs a Catmull-Rom spline
     * @param[in] wrapMode The wrapping behavior of the curve
     * @param[in] vstep Number of control points to step between curve segments
     */
    CatmullRom(eBasisCurveWrap wrapMode, uint32_t vstep) : SplineCurve(wrapMode, vstep)
    {
    }
    ~CatmullRom() override = default;

protected:
    /**
     * @brief Evaluates the Catmull-Rom basis functions
     * @details Computes the coefficients for both position and tangent using
     *          the Catmull-Rom spline basis matrix
     *
     * @param[in] u The parameter value (1-t)
     * @param[in] u2 The square of the parameter value (u^2)
     * @param[in] u3 The cube of the parameter value (u^3)
     * @return Coefficients for curve position and tangent calculation
     */
    coeff evalBasis(float u, float u2, float u3) override
    {
        coeff cf;
        cf.basis = pxr::GfVec4f(0.5f * u3 - 0.5f * u2, -1.5f * u3 + 2.0f * u2 + 0.5f * u, 1.5f * u3 - 2.5f * u2 + 1.0f,
                                -0.5f * u3 + u2 - 0.5f * u);
        cf.tangentBasis = pxr::GfVec4f(
            1.5f * u2 - u, -4.5f * u2 + 4.0f * u + 0.5f, 4.5f * u2 - 5.0f * u, -1.5f * u2 + 2.0f * u - 0.5f);

        return cf;
    }
};

/**
 * @brief B-spline curve implementation
 * @details A type of cubic spline that provides C2 continuity and local control.
 *          The curve generally does not pass through its control points but
 *          follows their shape smoothly.
 */
class BSpline : public SplineCurve
{
public:
    /**
     * @brief Constructs a B-spline curve
     * @param[in] wrapMode The wrapping behavior of the curve
     * @param[in] vstep Number of control points to step between curve segments
     */
    BSpline(eBasisCurveWrap wrapMode, uint32_t vstep) : SplineCurve(wrapMode, vstep)
    {
    }
    ~BSpline() override = default;

protected:
    /**
     * @brief Evaluates the B-spline basis functions
     * @details Computes the coefficients for both position and tangent using
     *          the cubic B-spline basis matrix
     *
     * @param[in] u The parameter value (1-t)
     * @param[in] u2 The square of the parameter value (u^2)
     * @param[in] u3 The cube of the parameter value (u^3)
     * @return Coefficients for curve position and tangent calculation
     */
    coeff evalBasis(float u, float u2, float u3) override
    {
        coeff cf;
        cf.basis =
            pxr::GfVec4f((1.0f / 6.0f) * u3, -0.5f * u3 + 0.5f * u2 + 0.5f * u + (1.0f / 6.0f),
                         0.5f * u3 - u2 + (2.0f / 3.0f), -(1.0f / 6.0f) * u3 + 0.5f * u2 - 0.5f * u + (1.0f / 6.0f));
        cf.tangentBasis = pxr::GfVec4f(0.5f * u2, -1.5f * u2 + u + 0.5f, 1.5f * u2 - 2.0f * u, -0.5f * u2 + u - 0.5f);

        return cf;
    }
};

/**
 * @brief Bezier curve implementation
 * @details A type of parametric curve that uses Bernstein polynomials as a basis.
 *          The curve is defined by its control points and provides intuitive
 *          geometric control over its shape.
 */
class Bezier : public SplineCurve
{
public:
    /**
     * @brief Constructs a Bezier curve
     * @param[in] wrapMode The wrapping behavior of the curve
     * @param[in] vstep Number of control points to step between curve segments
     */
    Bezier(eBasisCurveWrap wrapMode, uint32_t vstep) : SplineCurve(wrapMode, vstep)
    {
    }
    ~Bezier() override = default;

protected:
    /**
     * @brief Evaluates the Bezier basis functions
     * @details Computes the coefficients for both position and tangent using
     *          the cubic Bezier basis matrix (Bernstein polynomials)
     *
     * @param[in] u The parameter value (1-t)
     * @param[in] u2 The square of the parameter value (u^2)
     * @param[in] u3 The cube of the parameter value (u^3)
     * @return Coefficients for curve position and tangent calculation
     */
    coeff evalBasis(float u, float u2, float u3) override
    {
        coeff cf;
        cf.basis = pxr::GfVec4f(
            u3, -3.0f * u3 + 3.0f * u2, 3.0f * u3 - 6.0f * u2 + 3.0f * u, -1.0f * u3 + 3.0f * u2 - 3.0f * u + 1.0f);
        cf.tangentBasis =
            pxr::GfVec4f(3.0f * u2, -9.0f * u2 + 6.0f * u, 9.0f * u2 - 12.0f * u + 3.0f, -3.0f * u2 + 6.0f * u - 3.0f);

        return cf;
    }
};

const pxr::TfToken CurveBasisPrimToken("basis");
const pxr::TfToken UVToken("primvars:st");

/*
 *  Exposed class to Python
 */
/**
 * @class BasisCurves
 * @brief A class for managing and manipulating basis curves in USD stage.
 * @details
 * This class provides functionality to create, tessellate, and manipulate basis curves
 * in a USD stage. It supports different curve types including Bezier, CatmullRom, and BSpline,
 * and can generate mesh representations of the curves.
 *
 * The class is exposed to Python for scripting purposes and handles the creation
 * of curve meshes with specified widths and normals.
 */
class BasisCurves
{
public:
    /**
     * @brief Array of tessellated points representing the curve in 4D space.
     * @details Contains the discretized points along the curve, where each point
     * is represented as a GfVec4f (x, y, z, w).
     */
    pxr::VtArray<pxr::GfVec4f> tessellatedPoints;

    /**
     * @brief Array of tessellated tangent vectors for the curve in 4D space.
     * @details Contains the tangent vectors at each tessellated point,
     * represented as GfVec4f vectors.
     */
    pxr::VtArray<pxr::GfVec4f> tessellatedTangents;

    /**
     * @brief Constructs a BasisCurves object.
     * @param[in] stageId The USD stage ID where the curve exists.
     * @param[in] primPath The primitive path for the curve in the USD stage.
     * @param[in] meshPrimPath The primitive path for the mesh representation.
     * @param[in] stepSize The tessellation step size (default: 0.1).
     * @details
     * Creates a BasisCurves object that manages a curve primitive in the USD stage.
     * The constructor initializes the appropriate curve type (Bezier, CatmullRom, or BSpline)
     * based on the primitive's attributes.
     */
    BasisCurves(long int stageId, const std::string& primPath, const std::string& meshPrimPath, const float stepSize = 0.1)
    {
        m_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
        if (m_stage)
        {
            pxr::UsdPrim prim = m_stage->GetPrimAtPath(pxr::SdfPath(primPath));
            pxr::UsdPrim meshPrim = m_stage->GetPrimAtPath(pxr::SdfPath(meshPrimPath));

            if (prim.IsValid() && meshPrim.IsValid() && prim.HasAttribute(CurveBasisPrimToken))
            {
                m_primCurve = pxr::UsdGeomBasisCurves(prim);
                m_mesh = pxr::UsdGeomMesh(meshPrim);
                pxr::TfToken type;
                m_primCurve.GetBasisAttr().Get(&type);
                pxr::TfToken wrap;
                m_primCurve.GetWrapAttr().Get(&wrap);

                eBasisCurveType curveType = stringToCurveType(type.GetString());
                eBasisCurveWrap wrapMode = stringToWrapType(wrap.GetString());
                if (curveType == eBasisCurveType::Bezier)
                {
                    m_curve = new Bezier(wrapMode, 3);
                }
                else if (curveType == eBasisCurveType::CatmullRom)
                {
                    // force pinned for this type of curve
                    wrapMode = eBasisCurveWrap::Pinned;
                    m_curve = new CatmullRom(wrapMode, 1);
                }
                else if (curveType == eBasisCurveType::BSpline)
                {
                    m_curve = new BSpline(wrapMode, 1);
                }
                m_curve->m_stepSize = stepSize;
            }
            else
            {
                std::cout << "Did not find all required primitives" << std::endl;
            }
        }
    }

    ~BasisCurves()
    {
        delete m_curve;
    }

    /**
     * @brief Tessellates the curve into discrete points and tangents.
     * @return The number of tessellated points generated.
     * @details
     * This function performs the tessellation of the curve, generating discrete points
     * and tangents along the curve path. It also creates a mesh representation of the
     * curve using the specified width and normal attributes from the USD primitive.
     *
     * The function clears existing tessellated points and tangents before generating
     * new ones. It only supports ribbon-style curves (curves with normal attributes)
     * and does not support tube-style curves.
     *
     * @note The function requires valid normal and width attributes in the USD primitive.
     * @return Returns 0 if tessellation fails, otherwise returns the number of tessellated points.
     */
    size_t tessellateCurve()
    {
        tessellatedPoints.clear();
        tessellatedTangents.clear();

        if (m_stage && m_curve && m_mesh)
        {
            // pull data from curve
            pxr::VtArray<pxr::GfVec3f> normals;
            pxr::UsdAttribute normalsAttr = m_primCurve.GetNormalsAttr();
            if (!normalsAttr.Get(&normals))
            {
                // If the curve prim has no normals it is considered a tube.
                // We only support ribbon style currently
                std::cout << "We do not currently support tubes" << std::endl;
                return 0;
            }

            pxr::VtArray<float> widths;
            pxr::UsdAttribute widthsAttr = m_primCurve.GetWidthsAttr();
            if (!widthsAttr.Get(&widths))
            {
                std::cout << "Failed to get width of the curve" << std::endl;
                return 0;
            }

            pxr::VtArray<pxr::GfVec3f> ctrlPoints;
            pxr::UsdAttribute pointsAttr = m_primCurve.GetPointsAttr();
            if (!pointsAttr.Get(&ctrlPoints))
            {
                std::cout << "Failed to get control points of the curve" << std::endl;
                return 0;
            }

            m_curve->tessellate(ctrlPoints, tessellatedPoints, tessellatedTangents);
            // we do not support varying width and normal currently
            if (tessellatedPoints.size() > 1)
            {
                createCurveMesh(widths[0] / 2, normals[0].GetNormalized(), tessellatedPoints, tessellatedTangents);
            }
        }

        return tessellatedPoints.size();
    }

    /**
     * Compute a curve length based on the tesselated points
     */
    static float getCurveLength(pxr::VtArray<pxr::GfVec4f>& points)
    {
        int32_t numPoints = static_cast<int32_t>(points.size());

        const float* pointPtr = points[0].data();

        pxr::GfVec3f cpPrev = { pointPtr[0], pointPtr[1], pointPtr[2] };

        float length = 0;
        for (int32_t i = 1; i < numPoints; ++i)
        {
            const float* curPointPtr = points[i].data();
            pxr::GfVec3f cpCur = { curPointPtr[0], curPointPtr[1], curPointPtr[2] };

            length += (cpCur - cpPrev).GetLength();
            cpPrev = cpCur;
        }

        return length;
    }

    /**
     * @brief Creates a mesh representation of the curve.
     * @param[in] width Half-width of the curve ribbon.
     * @param[in] normal The normal vector for the curve ribbon orientation.
     * @param[in] tessellatedPoints Array of tessellated points along the curve.
     * @param[in] tessellatedTangents Array of tangent vectors at tessellated points.
     * @details
     * Creates a mesh representation of the curve as a ribbon with the specified width
     * and orientation. The mesh is generated using the tessellated points and tangents,
     * creating a ribbon-like surface that follows the curve path.
     */
    void createCurveMesh(float width,
                         pxr::GfVec3f normal,
                         pxr::VtArray<pxr::GfVec4f>& tessellatedPoints,
                         pxr::VtArray<pxr::GfVec4f>& tessellatedTangents)
    {
        int32_t numTessellatedPoints = static_cast<int32_t>(tessellatedPoints.size());
        // reserve arrays
        pxr::VtArray<pxr::GfVec3f> meshPoints(numTessellatedPoints * 2);
        // Init with the only normal we use
        pxr::VtArray<pxr::GfVec3f> meshNormals(numTessellatedPoints * 2, normal);
        // texture coordinates
        pxr::VtArray<pxr::GfVec2f> meshTexCoords(numTessellatedPoints * 2);
        // Index array for quad primitives
        pxr::VtArray<int> meshIndices;
        // Primitive count array
        pxr::VtArray<int> meshFaceCount;

        // Get curve length for textur coordinate generation
        float curveLength = getCurveLength(tessellatedPoints);
        float currentCurveLength = 0;
        // We use currently a hard coded texture scale param.
        float texScale = 1;

        // start point
        const float* tangentPtr = tessellatedTangents[0].data();
        pxr::GfVec3f tangent = { tangentPtr[0], tangentPtr[1], tangentPtr[2] };
        pxr::GfVec3f binormal = getOrientation(normal, tangent);
        pxr::GfVec3f offset = binormal * width;
        const float* pointPtr = tessellatedPoints[0].data();
        pxr::GfVec3f cp = { pointPtr[0], pointPtr[1], pointPtr[2] };
        size_t meshPointIndex = 0;
        meshPoints[meshPointIndex++] = cp - offset;
        meshPoints[meshPointIndex++] = cp + offset;

        for (int32_t i = 1; i < numTessellatedPoints; ++i)
        {
            const float* pointPtr = tessellatedPoints[i].data();
            const float* tangentPtr = tessellatedTangents[i].data();

            pxr::GfVec3f cpi = { pointPtr[0], pointPtr[1], pointPtr[2] };
            tangent = { tangentPtr[0], tangentPtr[1], tangentPtr[2] };
            binormal = getOrientation(normal, tangent);
            offset = binormal * width;

            meshTexCoords[meshPointIndex] = pxr::GfVec2f(0, (currentCurveLength / curveLength) * texScale);
            meshPoints[meshPointIndex++] = cpi - offset;
            meshTexCoords[meshPointIndex] = pxr::GfVec2f(1, (currentCurveLength / curveLength) * texScale);
            meshPoints[meshPointIndex++] = cpi + offset;

            // compute texture coordinates based on total curve length and current run length
            currentCurveLength += (cp - cpi).GetLength();
            cp = cpi; // store as previous point

            // Indices
            int top = i - 1;
            int top_left = top * 2;
            int top_right = top * 2 + 1;
            int bottom_left = i * 2;
            int bottom_right = i * 2 + 1;
            meshIndices.push_back(top_left);
            meshIndices.push_back(top_right);
            meshIndices.push_back(bottom_right);
            meshIndices.push_back(bottom_left);
            // new quad
            meshFaceCount.push_back(4);
        }

        // Set usd mesh values
        m_mesh.CreatePointsAttr().Set(meshPoints);
        m_mesh.CreateNormalsAttr().Set(meshNormals);
        m_mesh.CreateFaceVertexIndicesAttr().Set(meshIndices);
        m_mesh.CreateFaceVertexCountsAttr().Set(meshFaceCount);
        pxr::UsdGeomPrimvarsAPI primvarsAPI(m_mesh);
        pxr::UsdGeomPrimvar uvPrimvar =
            primvarsAPI.CreatePrimvar(UVToken, pxr::SdfValueTypeNames->Float2Array, pxr::UsdGeomTokens->faceVarying);
        if (uvPrimvar)
        {
            uvPrimvar.Set(meshTexCoords);
            uvPrimvar.SetIndices(meshIndices);
        }
    }

private:
    static eBasisCurveType stringToCurveType(const std::string& type)
    {
        eBasisCurveType enumType = eBasisCurveType::CatmullRom;
        if (type == std::string("bezier"))
        {
            enumType = eBasisCurveType::Bezier;
        }
        else if (type == std::string("catmullrom"))
        {
            enumType = eBasisCurveType::CatmullRom;
        }
        else if (type == std::string("bspline"))
        {
            enumType = eBasisCurveType::BSpline;
        }

        return enumType;
    }

    static eBasisCurveWrap stringToWrapType(const std::string& type)
    {
        eBasisCurveWrap enumType = eBasisCurveWrap::NonPeriodic;
        if (type == std::string("periodic"))
        {
            enumType = eBasisCurveWrap::Periodic;
        }
        else if (type == std::string("nonperiodic"))
        {
            enumType = eBasisCurveWrap::NonPeriodic;
        }
        else if (type == std::string("pinned"))
        {
            enumType = eBasisCurveWrap::Pinned;
        }

        return enumType;
    }

    static pxr::GfVec3f getOrientation(pxr::GfVec3f& normal, pxr::GfVec3f& tangent)
    {
        pxr::GfVec3f binormal = GfCross(tangent.GetNormalized(), normal);
        return binormal.GetNormalized();
    }

    SplineCurve* m_curve = nullptr;
    pxr::UsdStageRefPtr m_stage = nullptr;
    pxr::UsdGeomBasisCurves m_primCurve;
    pxr::UsdGeomMesh m_mesh;
};

}
}
}
}
