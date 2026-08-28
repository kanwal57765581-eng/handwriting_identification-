from flask import Flask, request, jsonify
import torch
from transformers import ViTImageProcessor, ViTForImageClassification
from PIL import Image
import pickle
from torchvision import transforms
import io
from flask_cors import CORS
from pymongo import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from torchvision import models

app = Flask(__name__)
CORS(app)

# ----------------------------------------
# Load Pre-trained Model (657 IAM Authors)
# ----------------------------------------
model_path = r'D:\FYP\fyp_handwritten\Ink_Identity_recogniser\model\model_seed42.pkl'

with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

model_state_dict = model_data["model_state_dict"]
label_to_id = model_data["label_to_id"]
id_to_label = {v: k for k, v in label_to_id.items()}

feature_extractor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')

model = ViTForImageClassification.from_pretrained(
    'google/vit-base-patch16-224',
    num_labels=len(label_to_id),
    ignore_mismatched_sizes=True
)
model.load_state_dict(model_state_dict)
model.eval()

# ----------------------------------------
# Load ResNet50 For New Author Registration
# ----------------------------------------
resnet = models.resnet50(weights='IMAGENET1K_V1')
resnet = torch.nn.Sequential(*list(resnet.children())[:-1])
resnet.eval()

# ----------------------------------------
# MongoDB Connection (For New Authors)
# ----------------------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["ink_identifier"]
collection = db["new_authors"]

# ----------------------------------------
# Image Preprocessing
# ----------------------------------------
augmentations = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
])

resnet_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ----------------------------------------
# Helper Functions
# ----------------------------------------

def preprocess_image(image):
    """Preprocess for ViT model (657 IAM authors)"""
    image = image.convert('RGB')
    image = augmentations(image)
    encoding = feature_extractor(
        images=image,
        return_tensors='pt',
        do_rescale=False
    )
    return encoding

def predict_author_iam(image):
    """Predict from 657 IAM authors using pre-trained model"""
    encoding = preprocess_image(image)
    with torch.no_grad():
        outputs = model(**encoding)
    logits = outputs.logits
    probs = torch.softmax(logits, dim=-1)
    confidence = probs.max().item()
    pred_id = logits.argmax(-1).item()
    author = id_to_label[pred_id]
    return author, round(confidence * 100, 2)

def extract_features_resnet(image):
    """Extract features using ResNet50 for new authors"""
    image = image.convert('RGB')
    img_tensor = resnet_transform(image).unsqueeze(0)
    with torch.no_grad():
        features = resnet(img_tensor)
    return features.squeeze().numpy().tolist()

def predict_new_author(features):
    """Match against new registered authors in MongoDB"""
    authors = list(collection.find())
    if not authors:
        return None, 0

    best_match = None
    best_score = -1

    for author in authors:
        for stored_vector in author["feature_vectors"]:
            # Make sure both are same size
            stored = np.array(stored_vector).reshape(1, -1)
            new = np.array(features).reshape(1, -1)

            # Skip if dimensions dont match
            if stored.shape[1] != new.shape[1]:
                continue

            score = cosine_similarity(new, stored)[0][0]
            if score > best_score:
                best_score = score
                best_match = author["author_name"]

    if best_match is None:
        return None, 0

    confidence = round(float(best_score) * 100, 2)
    return best_match, confidence

# ----------------------------------------
# Routes
# ----------------------------------------

# EXISTING ROUTE — Compare 2 samples
@app.route('/predict', methods=['POST'])
def predict():
    if 'image1' not in request.files or 'image2' not in request.files:
        return jsonify({
            'error': 'Both image1 and image2 are required'
        }), 400

    image1 = Image.open(request.files['image1'].stream)
    image2 = Image.open(request.files['image2'].stream)

    author1, conf1 = predict_author_iam(image1)
    author2, conf2 = predict_author_iam(image2)

    return jsonify({
        'author1': author1,
        'author2': author2,
        'confidence1': f"{conf1}%",
        'confidence2': f"{conf2}%"
    })


# NEW ROUTE — Register new author on the spot
@app.route('/register', methods=['POST'])
def register():
    try:
        author_name = request.form.get('author_name')
        file = request.files.get('image')

        if not author_name or not file:
            return jsonify({
                'error': 'Author name and image are required!'
            }), 400

        image = Image.open(file.stream)
        features = extract_features_resnet(image)

        # Check if author already exists
        existing = collection.find_one({"author_name": author_name})
        if existing:
            collection.update_one(
                {"author_name": author_name},
                {"$push": {"feature_vectors": features}}
            )
        else:
            collection.insert_one({
                "author_name": author_name,
                "feature_vectors": [features]
            })

        return jsonify({
            'message': f"Author '{author_name}' registered successfully!"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# NEW ROUTE — Identify writer from 657 + new authors
@app.route('/identify', methods=['POST'])
def identify():
    try:
        file = request.files.get('image')

        if not file:
            return jsonify({'error': 'Image is required!'}), 400

        image = Image.open(file.stream)

        # Extract features using ResNet50
        features = extract_features_resnet(image)

        # Check against new registered authors in MongoDB
        new_author, new_confidence = predict_new_author(features)

        # Also check against IAM authors using ViT model
        iam_author, iam_confidence = predict_author_iam(image)

        # Return best match
        if new_author and new_confidence > iam_confidence:
            return jsonify({
                'author': new_author,
                'confidence': f"{new_confidence}%",
                'source': 'Registered Author'
            })
        else:
            return jsonify({
                'author': iam_author,
                'confidence': f"{iam_confidence}%",
                'source': 'IAM Dataset (657 Authors)'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# NEW ROUTE — Get all registered authors
@app.route('/get_authors', methods=['GET'])
def get_authors():
    try:
        authors = [a["author_name"] for a in collection.find()]
        return jsonify({'authors': authors})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)