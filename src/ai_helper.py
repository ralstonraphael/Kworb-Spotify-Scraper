"""AI helper module for processing Spotify chart data."""
import logging
import os
from typing import Dict, List, Optional
import openai
import streamlit as st

logger = logging.getLogger(__name__)

class AIHelper:
    """Helper class for AI-powered data processing."""
    
    def __init__(self):
        """Initialize the AI helper."""
        # Try to get API key from environment variable first
        api_key = os.getenv("OPENAI_API_KEY")
        
        # If not found in environment, try Streamlit secrets
        if not api_key and hasattr(st, "secrets"):
            api_key = st.secrets.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set it in your environment variables "
                "or Streamlit secrets with the key 'OPENAI_API_KEY'"
            )
        
        # Set the API key for the OpenAI client
        openai.api_key = api_key
        logger.info("OpenAI API key configured successfully")

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
            
            response = openai.chat.completions.create(
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