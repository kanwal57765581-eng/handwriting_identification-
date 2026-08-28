import os
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
from transformers import TrainingArguments, Trainer
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
import numpy as np
import pickle
import torch.nn as nn
import torch.optim as optim

device = torch.device("cpu")  # Force CPU usage



data_dir =  r"D:\FYP\fyp_handwritten\Ink_Identity_recogniser\data" # Adjust the path as needed


model_save_dir =  r"D:\FYP\fyp_handwritten\Ink_Identity_recogniser\model"
model_save_path = os.path.join(model_save_dir, "model_seed42.pkl")

os.makedirs(model_save_dir, exist_ok=True)


def load_image_paths_labels(data_dir):
    image_paths = []
    labels = []
    author_image_count = {}

    for author in os.listdir(data_dir):
        author_dir = os.path.join(data_dir, author)
        if os.path.isdir(author_dir):
            image_count = 0
            temp_image_paths = []
            for img_name in os.listdir(author_dir):
                if img_name.endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(author_dir, img_name)
                    temp_image_paths.append(image_path)
                    image_count += 1

            if image_count >= 3:
                image_paths.extend(temp_image_paths)
                labels.extend([author] * image_count)
                author_image_count[author] = image_count

    print(f"Authors with 3 or more images: {len(author_image_count)}")
    return pd.DataFrame({'image_path': image_paths, 'label': labels})


df = load_image_paths_labels(data_dir)


label_to_id = {label: idx for idx, label in enumerate(df['label'].unique())}
df['label'] = df['label'].map(label_to_id)


train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])


augmentations = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
])


class HandwritingDataset(Dataset):
    def __init__(self, dataframe, transforms=None):
        self.dataframe = dataframe
        self.transforms = transforms

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        img_path = self.dataframe.iloc[idx]['image_path']
        label = self.dataframe.iloc[idx]['label']
        image = Image.open(img_path).convert('RGB')

        if self.transforms:
            image = self.transforms(image)

        return image, label


resnet = models.resnet50(weights='IMAGENET1K_V1')
resnet = torch.nn.Sequential(*(list(resnet.children())[:-1]))  
resnet = resnet.to(device)  


def extract_features(model, dataloader):
    model.eval()
    features = []
    labels = []
    with torch.no_grad():
        for images, label in dataloader:
            images = images.to(device) 
            output = model(images).cpu()  
            features.append(output.squeeze().numpy())
            labels.append(label.numpy())
    features = np.concatenate(features)
    labels = np.concatenate(labels)
    return features, labels


train_dataset = HandwritingDataset(train_df, transforms=augmentations)
test_dataset = HandwritingDataset(test_df, transforms=augmentations)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)


train_features, train_labels = extract_features(resnet, train_loader)
test_features, test_labels = extract_features(resnet, test_loader)


np.save(os.path.join(model_save_dir, 'train_features.npy'), train_features)
np.save(os.path.join(model_save_dir, 'train_labels.npy'), train_labels)
np.save(os.path.join(model_save_dir, 'test_features.npy'), test_features)
np.save(os.path.join(model_save_dir, 'test_labels.npy'), test_labels)


train_features = np.load(os.path.join(model_save_dir, 'train_features.npy'))
train_labels = np.load(os.path.join(model_save_dir, 'train_labels.npy'))
test_features = np.load(os.path.join(model_save_dir, 'test_features.npy'))
test_labels = np.load(os.path.join(model_save_dir, 'test_labels.npy'))


class FeatureDataset(Dataset):
    def __init__(self, features, labels):
        self.features = features
        self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        feature = torch.tensor(self.features[idx], dtype=torch.float32)
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return feature, label

train_dataset = FeatureDataset(train_features, train_labels)
test_dataset = FeatureDataset(test_features, test_labels)

class SimpleClassifier(nn.Module):
    def __init__(self, input_dim, num_classes):
        super(SimpleClassifier, self).__init__()
        self.fc = nn.Linear(input_dim, num_classes)

    def forward(self, x):
        return self.fc(x)


input_dim = train_features.shape[1]
num_classes = len(label_to_id)
model = SimpleClassifier(input_dim, num_classes)
model = model.to(device) 


criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


def train_model(model, train_loader, criterion, optimizer, num_epochs):
    model.train()
    for epoch in range(num_epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        for features, labels in train_loader:
            features, labels = features.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss/len(train_loader):.4f}, Accuracy: {100*correct/total:.2f}%')
    return model


train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)


num_epochs = 45
trained_model = train_model(model, train_loader, criterion, optimizer, num_epochs)


trained_model = trained_model.cpu()


model_data = {
    "model_state_dict": trained_model.state_dict(),
    "label_to_id": label_to_id
}
model_save_path = os.path.join(model_save_dir, "model.pkl")
with open(model_save_path, 'wb') as f:
    pickle.dump(model_data, f)

print(f"Model saved at: {model_save_path}")


with open(model_save_path, 'rb') as f:
    model_data = pickle.load(f)

model_state_dict = model_data["model_state_dict"]
label_to_id = model_data["label_to_id"]


model = SimpleClassifier(input_dim, num_classes)
model.load_state_dict(model_state_dict)



