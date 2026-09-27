import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

# 1. Create our training dataset
data = {
    "temperature": [72, 95, 68, 101, 75, 98, 70, 105, 80, 92],
    "vibration": [2.1, 5.8, 1.8, 6.4, 2.5, 5.5, 2.0, 7.0, 3.0, 5.1],
    "pressure": [4.2, 4.5, 4.0, 5.1, 4.1, 4.8, 4.0, 5.2, 4.3, 4.7],
    "hours_used": [1200, 2100, 900, 2500, 1300, 2200, 1000, 2800, 1500, 2000],
    "fault": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)

print("Dataset:")
print(df)

# 2. Separate features and target
X = df[["temperature", "vibration", "pressure", "hours_used"]]
y = df["fault"]

# 3. Split data into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4. Create the ML model
model = DecisionTreeClassifier(random_state=42)

# 5. Train the model
model.fit(X_train, y_train)

# 6. Make predictions
predictions = model.predict(X_test)

# 7. Check accuracy
accuracy = accuracy_score(y_test, predictions)

print("\nPredictions:")
print(predictions)

print("\nActual values:")
print(y_test.values)

print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

new_machine = [[100, 6.0, 4.9, 2400]]

new_prediction = model.predict(new_machine)

print("\nNew machine prediction:")

if new_prediction[0] == 1:
    print("⚠️ Potential fault detected")
else:
    print("✅ Machine condition appears normal")