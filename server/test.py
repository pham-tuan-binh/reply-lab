from pathlib import Path
from modules import generate_kmz, parse_drone_command


# Get the current working directory
WORKING_DIR = Path(__file__).resolve().parent

# Define the path to the test directory
TEST_DIR = WORKING_DIR / "data" / "test"
IMAGE_DIR = TEST_DIR/ "images"
LABEL_DIR = TEST_DIR / "labels"

TEST_OUTPUT_DIR = WORKING_DIR / "output"

# Get kmz
generate_kmz(IMAGE_DIR, LABEL_DIR, TEST_OUTPUT_DIR)