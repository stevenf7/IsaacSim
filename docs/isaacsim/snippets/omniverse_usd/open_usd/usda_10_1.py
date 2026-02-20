new_shader = UsdShade.Shader.Get(stage, "/hello/material/Shader")
new_shader.GetInput("diffuse_color_constant").Set(Gf.Vec3f(0, 0, 1))
