# load_dataset.py
# Run this ONCE to load all 657 authors into MongoDB

import os
import torch
import numpy as np
from PIL import Image
from torchvision import models, transforms
from pymongo import MongoClient

# ----------------------------------------
# Setup
# ----------------------------------------

# Your IAM dataset path
DATA_DIR = r"D:\FYP\fyp_handwritten\Ink_Identity_recogniser\data"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["ink_identifier"]
collection = db["iam_authors"]  # separate collection for IAM authors

# ----------------------------------------
# Load ResNet50 for feature extraction
# ----------------------------------------
print("Loading ResNet50 model...")
resnet = models.resnet50(weights='IMAGENET1K_V1')
resnet = torch.nn.Sequential(*list(resnet.children())[:-1])
resnet.eval()

# Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ----------------------------------------
# Feature extraction function
# ----------------------------------------
def extract_features(image_path):
    try:
        img = Image.open(image_path).convert('RGB')
        img_tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            features = resnet(img_tensor)
        return features.squeeze().numpy().tolist()
    except Exception as e:
        print(f"Error extracting features from {image_path}: {e}")
        return None

# ----------------------------------------
# Load all authors from dataset
# ----------------------------------------
def load_all_authors():
    # Clear existing IAM authors
    collection.drop()
    print("Cleared existing IAM authors collection")

    authors = os.listdir(DATA_DIR)
    total_authors = len(authors)
    loaded = 0
    skipped = 0

    print(f"Found {total_authors} author folders")
    print("Starting to load authors into MongoDB...")
    print("-" * 50)

    for author in authors:
        author_dir = os.path.join(DATA_DIR, author)

        # Skip if not a folder
        if not os.path.isdir(author_dir):
            continue

        # Get all images for this author
        images = [
            f for f in os.listdir(author_dir)
            if f.endswith(('.png', '.jpg', '.jpeg'))
        ]

        # Skip authors with less than 3 images
        if len(images) < 3:
            skipped += 1
            continue

        # Extract features for each image
        feature_vectors = []
        for img_name in images:
            img_path = os.path.join(author_dir, img_name)
            features = extract_features(img_path)
            if features:
                feature_vectors.append(features)

        # Save to MongoDB
        if feature_vectors:
            collection.insert_one({
                "author_name": author,
                "author_id": loaded,
                "total_samples": len(feature_vectors),
                "feature_vectors": feature_vectors,
                "source": "IAM_DATASET"
            })
            loaded += 1
            print(f"✅ Loaded author {loaded}/{total_authors}: "f"{author} ({len(feature_vectors)} samples)")

    print("-" * 50)
    print(f"✅ Done! Loaded {loaded} authors into MongoDB")
    print(f"⚠️  Skipped {skipped} authors (less than 3 samples)")

# ----------------------------------------
# Run
# ----------------------------------------
if __name__ == "__main__":
    load_all_authors()