import os.path as ops
import lightning as L
from components import PrivateAISyntheticData, PyTorchLightningScript, TextServeGradio

class TrainDeploy(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.input_path = "./datasets/test2.csv"
        self.output_path = "./datasets/test2_pai_output.csv"
        self.url = "http://localhost:8080/deidentify_text"
        self.key = "INTERNAL_TESTING_UNLIMITED_REALLY"
        self.mode = "standard"
        self.private_ai_synthetic_data = PrivateAISyntheticData(key=self.key, mode=self.mode
                                                                , text_feature="text",
                                                                url=self.url)
        self.private_ai_synthetic_data.run(input_text_or_path=self.input_path, action='batch',
                                           output_path=self.output_path)


        if self.private_ai_synthetic_data.output_path:
            self.train_work = PyTorchLightningScript(
                script_path=ops.join(ops.dirname(__file__), "./train_script.py"),
                script_args=["--trainer.max_epochs=1", f"--data.data_file={self.private_ai_synthetic_data.output_path}", "--data.text_feature=text"],
            )

        self.serve_work = TextServeGradio(cloud_compute=L.CloudCompute("cpu", 1))

    def run(self):

        # 1. Run the python script that trains the model
        self.train_work.run()

        # 2. when a checkpoint is available, deploy
        if self.train_work.best_model_path:
            self.serve_work.run(self.train_work.best_model_path)

    def configure_layout(self):
        tab_1 = {"name": "Model training", "content": self.train_work}
        tab_2 = {"name": "Interactive demo", "content": self.serve_work}
        return [tab_1, tab_2]

app = L.LightningApp(TrainDeploy())
