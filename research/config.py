import os

# Set these to False if the user has a working internet connection
# Used to prevent network errors in restricted environments
OFFLINE_MODE = True 

if OFFLINE_MODE:
    os.environ['HF_HUB_DISABLE_SSL_VERIFY'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "inbox")
DEST_DIR = os.path.join(BASE_DIR, "sorted")
INDEX_PATH = os.path.join(BASE_DIR, "file_index.pkl")

# Ensure directories exist
os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(DEST_DIR, exist_ok=True)

# Models
BI_ENCODER_MODEL = 'all-MiniLM-L6-v2'

# Feature Settings
MIN_FILES_FOR_STATS = 3
SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx'}

# Sorted Engine Parameters (Rank-Weighted k-NN)
K_NEIGHBORS = 5
DEPTH_WEIGHT = 0.08
CONFIDENCE_THRESHOLD = 0.5 # Auto-calibrated to 0.5 based on F1-Maximization
