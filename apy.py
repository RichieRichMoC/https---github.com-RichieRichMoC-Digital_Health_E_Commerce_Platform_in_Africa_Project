import streamlit as st
import pandas as pd

# Function to load and cache the dataset
@st.cache(allow_output_mutation=True)
def load_data():
    # Load the dataset from the Dataset folder
    df = pd.read_csv("./dataset/Data_on_Economic_Growth_indicatorProcessed.csv") 
    return df
def load_data2():
    # Load the dataset from the Dataset folder
    df2 = pd.read_csv("./dataset/Data_on_Non_Communicable_diseaseProcessed.csv") 
    return df2
def load_data3():
    # Load the dataset from the Dataset folder
    df3 = pd.read_csv("./dataset/Data_on_PopulationProcessed.csv") 
    return df3
def load_data4():
    # Load the dataset from the Dataset folder
    df4 = pd.read_csv("./dataset/Data_on_TechnologyProcessed.csv") 
    return df4
def main():
    # Load the dataset
    df = load_data()
   

    # Display the first few rows of the dataset
    st.write(df.head())

if __name__ == '__main__':
    main()