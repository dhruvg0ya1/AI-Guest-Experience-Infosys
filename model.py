from pymongo import MongoClient
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import xgboost as xgb
from sklearn.metrics import accuracy_score, log_loss
import matplotlib.pyplot as plt

# MongoDB Connection
client = MongoClient("mongodb+srv://dhruvg0yal:dhruv17goyal@cluster0.ghmci.mongodb.net/")
db = client["hotel_guests"]
collection = db["dining_info"]
df_from_mongo = pd.DataFrame(list(collection.find()))
df = df_from_mongo.copy()

# Data preprocessing
df['check_in_date'] = pd.to_datetime(df['check_in_date'])
df['check_out_date'] = pd.to_datetime(df['check_out_date'])
df['order_time'] = pd.to_datetime(df['order_time'])
df['check_in_day'] = df['check_in_date'].dt.dayofweek
df['check_out_day'] = df['check_out_date'].dt.dayofweek
df['check_in_month'] = df['check_in_date'].dt.month
df['check_out_month'] = df['check_out_date'].dt.month
df['stay_duration'] = (df['check_out_date'] - df['check_in_date']).dt.days

# Split data into features, train and test sets
features_df = df[df['order_time'] < '2024-01-01']
train_df = df[(df['order_time'] >= '2024-01-01') & (df['order_time'] <= '2024-10-01')]
test_df = df[df['order_time'] > '2024-10-01']

# Feature Engineering
# Customer level features
customer_features = features_df.groupby('customer_id').agg(
    avg_spend=('price_for_1', 'mean'),
    avg_stay_duration=('stay_duration', 'mean'),
    avg_qty=('Qty', 'mean')
).reset_index()

# Customer cuisine preferences
customer_fav_cuisine = features_df.groupby('customer_id')['Preferred Cusine'].agg(lambda x: x.mode()[0]).reset_index()
customer_frequent_cuisine = features_df.groupby('customer_id')['Preferred Cusine'].agg(lambda x: x.value_counts().idxmax()).reset_index()

# Customer dish preferences
customer_fav_dish = features_df.groupby('customer_id')['dish'].agg(lambda x: x.mode()[0]).reset_index()
customer_fav_dish.rename(columns={'dish': 'customer_fav_dish'}, inplace=True)
customer_frequent_dish = features_df.groupby('customer_id')['dish'].agg(lambda x: x.value_counts().idxmax()).reset_index()
customer_frequent_dish.rename(columns={'dish': 'customer_frequent_dish'}, inplace=True)

# Cuisine level features
cuisine_features = features_df.groupby('Preferred Cusine').agg(
    total_orders_per_cuisine=('transaction_id', 'count'),
    avg_spend_per_cuisine=('price_for_1', 'mean'),
    avg_qty_per_cuisine=('Qty', 'mean'),
    avg_stay_duration_per_cuisine=('stay_duration', 'mean')
).reset_index()

cuisine_popular_dish = features_df.groupby('Preferred Cusine')['dish'].agg(lambda x: x.mode()[0]).reset_index()
cuisine_popular_dish.rename(columns={'dish': 'cuisine_popular_dish'}, inplace=True)
cuisine_frequent_dish = features_df.groupby('Preferred Cusine')['dish'].agg(lambda x: x.value_counts().idxmax()).reset_index()
cuisine_frequent_dish.rename(columns={'dish': 'cuisine_frequent_dish'}, inplace=True)

# Merge features with train data
def merge_features(df):
    df = df.merge(customer_features, on='customer_id', how='left')
    df = df.merge(customer_fav_cuisine, on='customer_id', how='left')
    df = df.merge(customer_frequent_cuisine, on='customer_id', how='left')
    df = df.merge(customer_fav_dish, on='customer_id', how='left')
    df = df.merge(customer_frequent_dish, on='customer_id', how='left')
    
    df = df.merge(cuisine_features, on='Preferred Cusine', how='left')
    df = df.merge(cuisine_popular_dish, on='Preferred Cusine', how='left')
    df = df.merge(cuisine_frequent_dish, on='Preferred Cusine', how='left')
    return df

train_df = merge_features(train_df)
test_df = merge_features(test_df)

# Drop unnecessary columns
columns_to_drop = ['_id', 'transaction_id', 'customer_id', 'price_for_1',
                  'Qty', 'order_time', 'check_in_date', 'check_out_date']

train_df.drop(columns_to_drop, axis=1, inplace=True)
test_df.drop(columns_to_drop, axis=1, inplace=True)

# Convert object columns to category
for df in [train_df, test_df]:
    object_columns = df.select_dtypes(include=['object']).columns
    for col in object_columns:
        df[col] = df[col].astype('category')

# One-hot encoding
categorical_cols = ['Preferred Cusine', 'customer_fav_dish', 'cuisine_popular_dish']
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')

# Transform train data
encoded_train = encoder.fit_transform(train_df[categorical_cols])
encoded_train_df = pd.DataFrame(
    encoded_train, 
    columns=encoder.get_feature_names_out(categorical_cols)
)
train_df = pd.concat([train_df.drop(columns=categorical_cols), encoded_train_df], axis=1)

# Transform test data
encoded_test = encoder.transform(test_df[categorical_cols])
encoded_test_df = pd.DataFrame(
    encoded_test, 
    columns=encoder.get_feature_names_out(categorical_cols)
)
test_df = pd.concat([test_df.drop(columns=categorical_cols), encoded_test_df], axis=1)

train_df = train_df.dropna(subset=['dish'])
test_df = test_df.dropna(subset=['dish'])

# Prepare target variable
label_encoder = LabelEncoder()
train_df['dish'] = label_encoder.fit_transform(train_df['dish'])
test_df['dish'] = label_encoder.transform(test_df['dish'])

# Split features and target
X_train = train_df.drop(columns=['dish'])
y_train = train_df['dish']
X_test = test_df.drop(columns=['dish'])
y_test = test_df['dish']

# Train XGBoost model
xgb_model = xgb.XGBClassifier(
    objective="multi:softmax",
    eval_metric="mlogloss",
    learning_rate=0.1,
    max_depth=1,
    n_estimators=100,
    subsample=1,
    colsample_bytree=1,
    random_state=42,
    enable_categorical=True
)

# Fit and evaluate model
xgb_model.fit(X_train, y_train)
y_pred = xgb_model.predict(X_test)
y_pred_prob = xgb_model.predict_proba(X_test)

# Print metrics
print("\nModel Performance:")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"Log loss: {log_loss(y_test, y_pred_prob):.4f}")

# Plot feature importance
xgb.plot_importance(xgb_model, max_num_features=10)
plt.title("Top 10 Most Important Features")
plt.tight_layout()
plt.show()
