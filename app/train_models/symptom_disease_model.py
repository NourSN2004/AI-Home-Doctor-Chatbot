# train_models/knn_model.py
import joblib
import numpy as np

class SymptomDiseaseModel:
    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.all_symptoms = None
        self.y_encoded = None  # Encoded labels for training data

    def load_model(self, model_path='models/knn_model.pkl', encoder_path='models/label_encoder.pkl'):
        # Load the trained KNN model and label encoder
        self.model = joblib.load(model_path)
        self.label_encoder = joblib.load(encoder_path)

    def set_additional_attributes(self, all_symptoms, y_encoded):
        self.all_symptoms = all_symptoms
        self.y_encoded = y_encoded

    def predict_disease(self, symptoms_list):
        """
        Predicts diseases based on a list of symptoms.

        Args:
            symptoms_list (list): List of symptoms, e.g., ["itching", "skin rash"]

        Returns:
            dict: A dictionary containing either the disease confidences or an error message.
        """
        # Normalize symptom names in the dataset
        all_symptoms_normalized = [symptom.strip().lower() for symptom in self.all_symptoms]
        symptom_mapping = dict(zip(all_symptoms_normalized, self.all_symptoms))

        # Initialize input vector
        input_vector = [0] * len(self.all_symptoms)

        # Process input symptoms
        symptoms_normalized = [symptom.strip().lower() for symptom in symptoms_list]

        unrecognized_symptoms = []
        for symptom in symptoms_normalized:
            if symptom in symptom_mapping:
                idx = self.all_symptoms.index(symptom_mapping[symptom])
                input_vector[idx] = 1
            else:
                unrecognized_symptoms.append(symptom)

        if unrecognized_symptoms:
            error_message = f"Symptom(s) not recognized: {', '.join(unrecognized_symptoms)}. Please check the symptom names and try again."
            return {"error": error_message}

        # Convert to numpy array and reshape
        input_vector = np.array(input_vector).reshape(1, -1)

        # Find the k nearest neighbors
        neighbors = self.model.kneighbors(input_vector, return_distance=True)
        distances = neighbors[0][0]
        neighbor_indices = neighbors[1][0]
        neighbor_classes = self.model._y[neighbor_indices]
        neighbor_diseases = self.label_encoder.inverse_transform(neighbor_classes)

        # Count the occurrences of each class among neighbors
        class_counts = np.bincount(neighbor_classes, minlength=len(self.label_encoder.classes_))
        total_neighbors = class_counts.sum()

        # Calculate confidences for all diseases
        disease_confidences = []
        for cls_idx in np.nonzero(class_counts)[0]:
            disease_name = self.label_encoder.inverse_transform([cls_idx])[0]
            disease_confidence = class_counts[cls_idx] / total_neighbors
            disease_confidences.append((disease_name, disease_confidence))

        # Sort the diseases by confidence in descending order
        disease_confidences.sort(key=lambda x: x[1], reverse=True)

        result_string = "\nPossible diseases based on the symptoms:"
        for disease_name, disease_confidence in disease_confidences:
            result_string += f"\n- {disease_name}: {disease_confidence*100:.2f}% confidence"

        result_string += "\n\nPlease consult a healthcare professional for a definitive diagnosis."

        return {"result": result_string} , [disease_names for disease_names in disease_confidences]