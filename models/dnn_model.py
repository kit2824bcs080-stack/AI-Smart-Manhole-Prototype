"""
Deep Neural Network (DNN) Risk Prediction Model.
Architecture: Multi-Layer Perceptron (MLP) for multi-parameter non-linear risk classification.
Inputs: [gas_ppm, water_level_pct, temperature_c, humidity_pct, delta_gas, delta_water]
Outputs: Softmax probabilities over [SAFE, WARNING, CRITICAL]
"""

import os
import json
import numpy as np
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

WEIGHTS_FILE = Path(__file__).resolve().parent / "weights.json"
CLASSES = ["SAFE", "WARNING", "CRITICAL"]

class ManholeRiskDNN:
    def __init__(self):
        self.classes = CLASSES
        self.weights = []
        self.biases = []
        self.mean = None
        self.scale = None
        self.is_loaded = False
        self._ensure_model_trained()

    def _generate_synthetic_training_data(self, n_samples=3000):
        """
        Synthesize physically consistent sewer telemetry for training the DNN.
        Simulates nominal flows, toxic gas surges, flash floods, and hazardous compound states.
        """
        np.random.seed(42)
        X = []
        y = []

        for _ in range(n_samples):
            scenario_choice = np.random.choice(["safe", "warning", "critical"], p=[0.40, 0.35, 0.25])
            
            if scenario_choice == "safe":
                gas = np.random.uniform(0.5, 14.0)
                water = np.random.uniform(5.0, 38.0)
                temp = np.random.uniform(18.0, 32.0)
                humidity = np.random.uniform(45.0, 75.0)
                delta_gas = np.random.uniform(-1.5, 1.5)
                delta_water = np.random.uniform(-2.0, 2.0)
                label = 0  # SAFE

            elif scenario_choice == "warning":
                sub_type = np.random.choice(["gas_creep", "water_rising", "temp_humidity"])
                if sub_type == "gas_creep":
                    gas = np.random.uniform(16.0, 48.0)
                    water = np.random.uniform(15.0, 50.0)
                    temp = np.random.uniform(22.0, 36.0)
                    humidity = np.random.uniform(55.0, 80.0)
                    delta_gas = np.random.uniform(-0.5, 5.0)
                    delta_water = np.random.uniform(-1.0, 3.0)
                elif sub_type == "water_rising":
                    gas = np.random.uniform(5.0, 25.0)
                    water = np.random.uniform(42.0, 74.0)
                    temp = np.random.uniform(20.0, 32.0)
                    humidity = np.random.uniform(70.0, 88.0)
                    delta_gas = np.random.uniform(-0.5, 2.0)
                    delta_water = np.random.uniform(-0.5, 10.0)
                else:
                    gas = np.random.uniform(10.0, 30.0)
                    water = np.random.uniform(25.0, 55.0)
                    temp = np.random.uniform(36.0, 44.0)
                    humidity = np.random.uniform(78.0, 92.0)
                    delta_gas = np.random.uniform(-0.5, 2.5)
                    delta_water = np.random.uniform(-0.5, 4.0)
                label = 1  # WARNING

            else:  # critical
                sub_type = np.random.choice(["toxic_spike", "flash_flood", "compound_hazard"])
                if sub_type == "toxic_spike":
                    gas = np.random.uniform(52.0, 120.0)
                    water = np.random.uniform(20.0, 70.0)
                    temp = np.random.uniform(24.0, 42.0)
                    humidity = np.random.uniform(60.0, 95.0)
                    delta_gas = np.random.uniform(-1.0, 15.0)
                    delta_water = np.random.uniform(-1.0, 5.0)
                elif sub_type == "flash_flood":
                    gas = np.random.uniform(5.0, 45.0)
                    water = np.random.uniform(76.0, 99.0)
                    temp = np.random.uniform(18.0, 30.0)
                    humidity = np.random.uniform(85.0, 99.0)
                    delta_gas = np.random.uniform(-1.0, 3.0)
                    delta_water = np.random.uniform(-1.0, 20.0)
                else: # Compound hazard
                    gas = np.random.uniform(38.0, 90.0)
                    water = np.random.uniform(65.0, 95.0)
                    temp = np.random.uniform(38.0, 52.0)
                    humidity = np.random.uniform(88.0, 99.0)
                    delta_gas = np.random.uniform(0.0, 15.0)
                    delta_water = np.random.uniform(0.0, 15.0)
                label = 2  # CRITICAL

            X.append([gas, water, temp, humidity, delta_gas, delta_water])
            y.append(label)

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)

    def train_and_export_weights(self):
        """Train Deep MLP and export trained weights to JSON."""
        X, y = self._generate_synthetic_training_data(n_samples=4000)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Deep Multi-Layer Perceptron architecture (6 -> 32 -> 16 -> 8 -> 3)
        mlp = MLPClassifier(
            hidden_layer_sizes=(32, 16, 8),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            batch_size=64,
            learning_rate_init=0.005,
            max_iter=400,
            random_state=42
        )
        mlp.fit(X_scaled, y)

        exported_weights = {
            "mean": scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
            "weights": [coef.tolist() for coef in mlp.coefs_],
            "biases": [intercept.tolist() for intercept in mlp.intercepts_],
            "classes": CLASSES
        }

        with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
            json.dump(exported_weights, f, indent=2)

        self._load_from_dict(exported_weights)

    def _load_from_dict(self, data):
        self.mean = np.array(data["mean"], dtype=np.float32)
        self.scale = np.array(data["scale"], dtype=np.float32)
        self.weights = [np.array(w, dtype=np.float32) for w in data["weights"]]
        self.biases = [np.array(b, dtype=np.float32) for b in data["biases"]]
        self.is_loaded = True

    def _ensure_model_trained(self):
        if WEIGHTS_FILE.exists():
            try:
                with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._load_from_dict(data)
                return
            except Exception:
                pass
        self.train_and_export_weights()

    @staticmethod
    def _relu(x):
        return np.maximum(0, x)

    @staticmethod
    def _softmax(x):
        e_x = np.exp(x - np.max(x))
        return e_x / np.sum(e_x)

    def predict(self, gas_ppm, water_level_pct, temperature_c, humidity_pct, delta_gas=0.0, delta_water=0.0):
        """
        Perform high-speed pure NumPy DNN forward pass.
        Returns:
            dict containing risk_level, confidence, probabilities, and normalized inputs.
        """
        if not self.is_loaded:
            self._ensure_model_trained()

        x = np.array([gas_ppm, water_level_pct, temperature_c, humidity_pct, delta_gas, delta_water], dtype=np.float32)
        # Normalize
        x_norm = (x - self.mean) / (self.scale + 1e-7)

        # Forward pass through hidden layers with ReLU
        activation = x_norm
        for i in range(len(self.weights) - 1):
            z = np.dot(activation, self.weights[i]) + self.biases[i]
            activation = self._relu(z)

        # Output layer with Softmax
        logits = np.dot(activation, self.weights[-1]) + self.biases[-1]
        probs = self._softmax(logits)

        pred_idx = int(np.argmax(probs))
        risk_level = self.classes[pred_idx]
        confidence = float(probs[pred_idx])

        return {
            "risk_level": risk_level,
            "confidence": round(confidence, 4),
            "probabilities": {
                "SAFE": round(float(probs[0]), 4),
                "WARNING": round(float(probs[1]), 4),
                "CRITICAL": round(float(probs[2]), 4)
            },
            "vector": {
                "gas_ppm": float(gas_ppm),
                "water_level_pct": float(water_level_pct),
                "temperature_c": float(temperature_c),
                "humidity_pct": float(humidity_pct),
                "delta_gas": float(delta_gas),
                "delta_water": float(delta_water)
            }
        }

# Global Singleton Instance
dnn_engine = ManholeRiskDNN()
