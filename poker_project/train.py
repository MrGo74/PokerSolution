import pandas as pd
import json
import os

def load_and_preprocess_data(filepath=None):
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), 'poker_data.csv')
    df = pd.read_csv(filepath)

    # Parse the round_state JSON
    round_state_df = pd.json_normalize(df['round_state'].apply(json.loads))

    # Combine the dataframes
    df = pd.concat([df.drop('round_state', axis=1), round_state_df], axis=1)

    # Feature Engineering
    # Parse hole_card
    df['hole_card'] = df['hole_card'].apply(eval)
    df['hole_card_1'] = df['hole_card'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    df['hole_card_2'] = df['hole_card'].apply(lambda x: x[1] if isinstance(x, list) and len(x) > 1 else None)

    # Parse community_card
    def parse_community_cards(cards):
        if not isinstance(cards, list):
            return [None] * 5
        padded_cards = cards + [None] * (5 - len(cards))
        return padded_cards

    community_cards_df = df['community_card'].apply(parse_community_cards).apply(pd.Series)
    community_cards_df.columns = [f'community_card_{i+1}' for i in range(5)]
    df = pd.concat([df, community_cards_df], axis=1)

    # Encode cards
    def encode_card(card):
        if card is None:
            return 0
        ranks = '23456789TJQKA'
        suits = 'SCDH'
        rank = ranks.find(card[1]) + 2
        suit = suits.find(card[0]) + 1
        return suit * 100 + rank

    for col in ['hole_card_1', 'hole_card_2', 'community_card_1', 'community_card_2', 'community_card_3', 'community_card_4', 'community_card_5']:
        df[col] = df[col].apply(encode_card)

    # Select features and target
    features = ['hole_card_1', 'hole_card_2', 'community_card_1', 'community_card_2', 'community_card_3', 'community_card_4', 'community_card_5', 'pot.main.amount', 'round_count']
    target = 'action'

    df = df[features + [target]].dropna()

    print("Data loaded and preprocessed successfully.")
    print(df.head())
    print(df.columns)
    return df

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

def train_model(df):
    # Prepare data for training
    X = df.drop('action', axis=1)
    y = df['action']

    # Encode target variable
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")

    # Save the model and encoder
    import joblib
    model_path = os.path.join(os.path.dirname(__file__), 'poker_model.joblib')
    encoder_path = os.path.join(os.path.dirname(__file__), 'label_encoder.joblib')
    joblib.dump(model, model_path)
    joblib.dump(le, encoder_path)
    print("Model and label encoder saved.")

    return model

if __name__ == '__main__':
    data = load_and_preprocess_data()
    train_model(data)
