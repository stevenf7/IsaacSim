import omni.replicator.core as rep

annotator = rep.AnnotatorRegistry.get_annotator("IsaacCreateRTXLidarScanBuffer")
# Initialize the Annotator with the desired outputs.
# Note: This must be done before attaching the Annotator to a render product.
annotator.initialize(outputTimestamp=True, outputMaterialId=True)
