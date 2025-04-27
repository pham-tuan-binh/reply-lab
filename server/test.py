from pathlib import Path
from modules import generate_kmz, parse_drone_command, drone_object_detection


# Get the current working directory
WORKING_DIR = Path(__file__).resolve().parent

# Define the path to the test directory
TEST_DIR = WORKING_DIR / "data" / "test"
IMAGE_DIR = TEST_DIR/ "images"
LABEL_DIR = TEST_DIR / "labels"

TEST_OUTPUT_DIR = TEST_DIR / "output"

drone_object_detection(IMAGE_DIR, LABEL_DIR)
generate_kmz(IMAGE_DIR, LABEL_DIR, TEST_OUTPUT_DIR)