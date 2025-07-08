"""Script to process chart data with AI assistance."""
import pandas as pd
from pathlib import Path
from .ai_helper import AIHelper
from .cleaner import DataCleaner

def process_charts():
    """Process chart data with AI assistance."""
    print("Starting chart data processing with AI assistance...")
    
    # Initialize our helpers
    ai_helper = AIHelper()
    data_cleaner = DataCleaner()
    
    # Define paths
    raw_data_path = Path("data/raw/chart_2025-07-03.csv")
    processed_data_path = Path("data/processed/ai_processed_charts.csv")
    insights_path = Path("data/processed/ai_insights.txt")
    
    # Read the raw data
    print(f"\nReading data from {raw_data_path}...")
    raw_df = pd.read_csv(raw_data_path)
    
    # Convert DataFrame to list of dictionaries for AI processing
    raw_data = raw_df.to_dict('records')
    
    # Get AI insights about the data
    print("\nGetting AI insights about the data...")
    insights = ai_helper.analyze_chart_data(raw_data)
    
    if insights["status"] == "success":
        print("\n=== AI Insights ===")
        print(insights["insights"])
        # Save insights to file
        insights_path.parent.mkdir(parents=True, exist_ok=True)
        with open(insights_path, 'w') as f:
            f.write(insights["insights"])
        print(f"\nInsights saved to {insights_path}")
    
    # Use AI to clean and format the data
    print("\nCleaning and formatting data with AI assistance...")
    cleaned_data = ai_helper.clean_and_format_data(raw_data)
    
    # Convert cleaned data to DataFrame
    cleaned_df = pd.DataFrame(cleaned_data)
    
    # Get visualization suggestions
    print("\nGetting visualization suggestions...")
    viz_suggestions = ai_helper.suggest_visualizations(cleaned_df.dtypes.to_dict())
    if viz_suggestions:
        print("\n=== Recommended Visualizations ===")
        for suggestion in viz_suggestions:
            print(f"- {suggestion}")
    
    # Save processed data
    print(f"\nSaving processed data to {processed_data_path}...")
    processed_data_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(processed_data_path, index=False)
    
    print("\nProcessing completed successfully!")
    print(f"- Processed data saved to: {processed_data_path}")
    print(f"- AI insights saved to: {insights_path}")

if __name__ == "__main__":
    process_charts() 