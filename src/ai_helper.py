"""AI helper module for processing Spotify chart data."""
import logging
import os
from typing import Dict, List, Optional
import openai
import streamlit as st
import json
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIHelper:
    """Helper class for AI-powered analysis of chart data."""
    
    def __init__(self, api_key: str):
        """Initialize the AI helper."""
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=api_key)
    
    def analyze_track_data(self, data: List[Dict]) -> str:
        """
        Analyze track streaming data using OpenAI's API.
        Returns exactly 5 bullet points of key information.
        """
        try:
            # Convert data to a readable format
            data_str = json.dumps(data, indent=2)
            
            # Create the prompt
            prompt = f"""
            Analyze this Spotify streaming data and provide EXACTLY 5 key insights.
            Focus on:
            - Total streams and major milestones
            - Growth rate and trends
            - Peak performance periods
            - Market-specific highlights
            - Notable achievements
            
            Format as 5 bullet points ONLY. Keep each point to one line, data-driven and concise.
            Do not include any introduction or additional text.
            
            Data:
            {data_str}
            """
            
            # Get completion from OpenAI
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data analyst providing exactly 5 bullet points of key streaming performance insights. Be concise and data-driven."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Lower temperature for more consistent output
                max_tokens=200  # Reduced token limit for more concise output
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error analyzing data with AI: {e}")
            return "Error analyzing data. Please try again."

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
            logger.error(f"Error in AI data cleaning: {e}")
            return raw_data 