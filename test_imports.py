from tqdm import tqdm
from src import config
from src.cleaner import DataCleaner
from src.scraper import ChartScraper

print("All imports successful!")
print(f"tqdm version: {tqdm.__version__}")
print(f"Config file location: {config.__file__}") 