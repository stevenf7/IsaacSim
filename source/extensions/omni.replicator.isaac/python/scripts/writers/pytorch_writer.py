from omni.replicator.core import Writer, AnnotatorRegistry, BackendDispatch
import torch


class PytorchWriter(Writer):
    def __init__(self, listener, output_dir=None, device="cpu"):
        # If output directory is specified, writer will write annotated data to the given directory
        if output_dir:
            self.backend = BackendDispatch({"paths": {"out_dir": output_dir}})
            self._backend = self.backend
            self._output_dir = self.backend.output_dir
        else:
            self._output_dir = None
        self._frame_id = 0

        self.annotators = [AnnotatorRegistry.get_annotator("rgb")]
        self.listener = listener
        self.device = device

    def write(self, data: dict):
        if self._output_dir:
            # Write RGB data to output directory as png
            self._write_rgb(data)
        pytorch_rgb = self._convert_to_pytorch(data)
        self.listener.write_data({"pytorch_rgb": pytorch_rgb, "device": self.device})
        self._frame_id += 1

    def _write_rgb(self, data: dict):
        for annotator in data.keys():
            if annotator.startswith("rgb"):
                render_product_name = annotator.split("-")[-1]
                file_path = f"rgb_{self._frame_id}_{render_product_name}.png"
                self._backend.write_image(file_path, data[annotator])

    def _convert_to_pytorch(self, data: dict):
        if data is None:
            raise Exception("Data is Null")

        data_tensor = None
        for annotator in data.keys():
            if annotator.startswith("rgb"):
                if data_tensor is None:
                    data_tensor = torch.tensor(data[annotator], dtype=torch.int32, device=self.device).unsqueeze(0)
                else:
                    rgb_tensor = torch.tensor(data[annotator], dtype=torch.int32, device=self.device).unsqueeze(0)
                    data_tensor = torch.cat((data_tensor, rgb_tensor), dim=0)
        return data_tensor
