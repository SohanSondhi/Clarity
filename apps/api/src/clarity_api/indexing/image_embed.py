import numpy as np
from PIL import Image
from clarity_api.core import settings  # loads IMAGE_MODEL + IMAGE_BACKEND


class ImageEmbedder:
    def __init__(self):
        # Read backend + model from settings.py
        self.backend = settings.IMAGE_BACKEND
        self.model_path = settings.IMAGE_MODEL

        if self.backend == "torch":
            # TESTING PURPOSES
            # HuggingFace CLIP backend
            import torch
            from transformers import CLIPProcessor, CLIPModel

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = CLIPModel.from_pretrained(self.model_path).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(self.model_path)

        elif self.backend == "onnx":
            # SNAPDRAGON DEPLOYMENT
            # Qualcomm ONNX model backend
            import onnxruntime as ort

            self.session = ort.InferenceSession(self.model_path)
            self.input_name = self.session.get_inputs()[0].name
            #confirm which output layer gives embeddings
            self.output_name = self.session.get_outputs()[-2].name
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def embed(self, image_path: str) -> np.ndarray:
        """Generate an embedding vector for the given image."""
        img = Image.open(image_path).convert("RGB")

        if self.backend == "torch":
            # TESTING PURPOSES
            # HuggingFace CLIP embedding flow
            import torch
            inputs = self.processor(images=img, return_tensors="pt").to(self.device)
            with torch.no_grad():
                vec = self.model.get_image_features(**inputs)
            vec = vec.cpu().numpy().astype("float32")

        elif self.backend == "onnx":
            # SNAPDRAGON DEPLOYMENT
            # Preprocess + run ONNX model
            arr = np.array(img.resize((224, 224))).astype("float32") / 255.0
            arr = arr.transpose(2, 0, 1)  # HWC -> CHW
            arr = np.expand_dims(arr, axis=0)  # batch dimension
            vec = self.session.run([self.output_name], {self.input_name: arr})[0]

        # Normalize vector (cosine similarity works best on unit vectors)
        norm = np.linalg.norm(vec, axis=1, keepdims=True)
        vec = vec / (norm + 1e-10)  # 1e-10 = safety against div/0

        return vec