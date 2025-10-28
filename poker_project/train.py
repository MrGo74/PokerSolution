import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib

def train_model(filepath=None):
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), 'poker_data.csv')

    df = pd.read_csv(filepath)
    print("Data loaded successfully.")
    print(df.head())
    print(df.columns)

    # All columns except 'action' and 'amount' are features
    features = [col for col in df.columns if col not in ['action', 'amount']]
    target = 'action'

    X = df[features]
    y = df[target]

    # Handle potential missing values
    X = X.fillna(-1)

    # Encode target variable
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")

    # Save the model and encoder
    model_path = os.path.join(os.path.dirname(__file__), 'poker_model.joblib')
    encoder_path = os.path.join(os.path.dirname(__file__), 'label_encoder.joblib')
    joblib.dump(model, model_path)
    joblib.dump(le, encoder_path)
    print("Model and label encoder saved.")

    return model

if __name__ == '__main__':
    train_model()
