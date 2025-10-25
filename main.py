from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import uvicorn
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.preprocessing import FunctionTransformer
from log_transformer import LogTransformer  # Import the LogTransformer class

# Load the trained model
logistic_model = joblib.load("./Models/logistic_model.joblib")
random_forest_model = joblib.load("./Models/random_forest_model.joblib")

# Define input data model
class InputData(BaseModel):
    REGION: str
    TENURE: str
    MONTANT: float
    FREQUENCE_RECH: float
    REVENUE: float
    ARPU_SEGMENT: float
    FREQUENCE: float
    DATA_VOLUME: float
    ON_NET: float
    ORANGE: float
    TIGO: float
    REGULARITY: int
    FREQ_TOP_PACK: float

app = FastAPI()

# Define LogTransformer instance
log_transformer = LogTransformer()

# Numerical transformer with LogTransformer
numerical_pipeline = Pipeline(steps=[
    ('num_imputer', SimpleImputer(strategy='median')),
    ('log_transform', FunctionTransformer(log_transformer.transform)),
    ('scaler', StandardScaler())
])

# Categorical transformer
categorical_pipeline = Pipeline(steps=[
    ('cat_imputer', SimpleImputer(strategy='most_frequent')),
    ('cat_encoder', OneHotEncoder())
])

# Combine transformers
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_pipeline, ['MONTANT', 'FREQUENCE_RECH', 'REVENUE', 'ARPU_SEGMENT', 'FREQUENCE', 'DATA_VOLUME', 'ON_NET', 'ORANGE', 'TIGO', 'REGULARITY', 'FREQ_TOP_PACK']),
        ('cat', categorical_pipeline, ['REGION', 'TENURE'])
    ],
    remainder='drop'
)

# Combine the preprocessor with the classifier in a pipeline
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', logistic_model)  # or random_forest_model
])

# Prediction endpoint with logistic model
@app.post("/predict_with_logistic_model")
def predict_with_logistic_model(data: InputData):
    # Convert input data to DataFrame
    input_df = pd.DataFrame([data.model_dump()])
    
    # Make predictions
    prediction = pipeline.predict(input_df)
    probability = pipeline.predict_proba(input_df)

    # Prepare response
    result = "Churn" if prediction[0] == 1 else "No Churn"
    probability = probability.tolist()
        
    return {"prediction": result, "probability": probability}

# Prediction endpoint with random forest model
@app.post("/predict_with_random_forest_model")
def predict_with_random_forest_model(data: InputData):
    # Convert input data to DataFrame
    input_df = pd.DataFrame([data.model_dump()])
    
    # Make predictions
    prediction = pipeline.predict(input_df)
    probability = pipeline.predict_proba(input_df)

    # Prepare response
    result = "Churn" if prediction[0] == 1 else "No Churn"
    probability = probability.tolist()
        
    return {"prediction": result, "probability": probability}

# Run the FastAPI app
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)