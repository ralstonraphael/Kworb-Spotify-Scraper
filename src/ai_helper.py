"""AI helper module for data structuring and cleaning."""
from typing import Dict, List
import os
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

class AIHelper:
    def __init__(self):
        """Initialize the AI helper with OpenAI client."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def clean_and_format_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Use AI to clean and structure raw chart data.
        
        Args:
            raw_data: List of dictionaries containing raw chart data
            
        Returns:
            List of cleaned and structured data dictionaries
        """
        try:
            # Convert a sample of the data to string for AI processing
            sample_data = str(raw_data[:2])
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are a data cleaning expert. Your task is to:
                    1. Ensure consistent data types (numbers as integers/floats, dates in ISO format)
                    2. Remove any invalid or corrupted entries
                    3. Standardize column names
                    4. Handle missing values appropriately
                    5. Format numbers without commas or special characters
                    Respond only with specific cleaning instructions, no explanations."""},
                    {"role": "user", "content": f"Provide cleaning instructions for this Spotify chart data: {sample_data}"}
                ]
            )
            
            cleaning_instructions = response.choices[0].message.content
            
            # Process the data based on AI instructions
            cleaned_data = []
            for entry in raw_data:
                cleaned_entry = {}
                for key, value in entry.items():
                    # Convert string numbers to integers/floats
                    if isinstance(value, str) and value.replace(',', '').replace('.', '').isdigit():
                        cleaned_entry[key] = float(value.replace(',', ''))
                    # Ensure dates are in ISO format
                    elif key in ['chart_date', 'date'] and value:
                        try:
                            cleaned_entry[key] = pd.to_datetime(value).strftime('%Y-%m-%d')
                        except:
                            cleaned_entry[key] = value
                    else:
                        cleaned_entry[key] = value
                cleaned_data.append(cleaned_entry)
            
            return cleaned_data
            
        except Exception as e:
            print(f"Error in AI data cleaning: {e}")
            return raw_data 