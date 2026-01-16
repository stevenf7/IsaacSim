# register new augmented annotator that adds noise to rgba and then outputs to rgb to the ROS publisher can publish
# the image_gaussian_noise_warp variable can be replaced with image_gaussian_noise_np to use the cpu version. Ensure to update device to "cpu" if using the cpu version.
rep.annotators.register(
    name="rgb_gaussian_noise",
    annotator=rep.annotators.augment_compose(
        source_annotator=rep.annotators.get("rgb", device="cuda"),
        augmentations=[
            rep.annotators.Augmentation.from_function(
                image_gaussian_noise_warp, sigma=0.1, seed=1234, data_out_shape=(-1, -1, 3)
            ),
        ],
    ),
)
