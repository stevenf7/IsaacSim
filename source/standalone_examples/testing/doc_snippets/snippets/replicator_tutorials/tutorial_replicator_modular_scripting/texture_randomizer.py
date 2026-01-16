def _apply_behavior(self):
    for mat in self._texture_materials:
        shader = UsdShade.Shader(omni.usd.get_shader_from_material(mat.GetPrim(), get_prim=True))
        diffuse_texture = random.choice(self._texture_urls)
        shader.GetInput("diffuse_texture").Set(diffuse_texture)

        project_uvw = random.choices(
            [True, False], weights=[self._project_uvw_probability, 1 - self._project_uvw_probability]
        )[0]
        shader.GetInput("project_uvw").Set(bool(project_uvw))

        texture_scale = random.uniform(self._texture_scale_range[0], self._texture_scale_range[1])
        shader.GetInput("texture_scale").Set((texture_scale, texture_scale))

        texture_rotate = random.uniform(self._texture_rotate_range[0], self._texture_rotate_range[1])
        shader.GetInput("texture_rotate").Set(texture_rotate)
