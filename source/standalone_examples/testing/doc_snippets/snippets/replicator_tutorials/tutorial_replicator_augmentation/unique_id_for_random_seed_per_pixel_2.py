depth_annot_1 = rep.annotators.get("distance_to_camera")
depth_annot_1.augment(depth_aug)
depth_annot_2 = rep.annotators.get("distance_to_camera")
depth_annot_2.augment(depth_aug, sigma=0.5)

rgb_to_bgr_annot.attach(rp)
depth_annot_1.attach(rp)
depth_annot_2.attach(rp)

# ...

await rep.orchestrator.step_async(rt_subframes=32)
rgb_data = rgb_to_bgr_annot.get_data()
depth_data_1 = depth_annot_1.get_data()
depth_data_2 = depth_annot_2.get_data()
