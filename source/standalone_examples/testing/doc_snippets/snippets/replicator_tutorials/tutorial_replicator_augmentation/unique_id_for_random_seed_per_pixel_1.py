rgb_to_bgr_annot = rep.annotators.augment(
    source_annotator=rep.annotators.get("rgb"),
    augmentation=rgb_to_bgr_augm,
)
