from nltk.corpus import stopwords
import nltk
from pdfminer.high_level import extract_text
import torch
import os
import faiss
import re
import numpy as np
from transformers import AutoTokenizer, DistilBertTokenizer, AutoModel
from summarizer import generate_message

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = extract_text(file)
    return reader

def remove_stop_words(text):
    stop_words = set(stopwords.words('english'))
    words = text.split()
    filtered_text = ' '.join([word for word in words if word.lower() not in stop_words])
    return filtered_text

def remove_special_characters(text):
    return re.sub(r'[^A-Za-z0-9\s]', '', text)

def generate_embeddings(text):
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    
    embeddings = outputs.last_hidden_state.mean(dim=1)
    
    return embeddings.numpy()

def extraction_and_summarization(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    text = remove_stop_words(text)
    
    model_ckpt = "distilbert-base-uncased"
    tokenizer = DistilBertTokenizer.from_pretrained(model_ckpt)
    encoded_text = tokenizer.encode(text, return_tensors="pt", max_length=512, truncation=True)
    tokens = tokenizer.convert_ids_to_tokens(encoded_text[0])
    
    arr = []
    for token in tokens:
        if "#" in token or "@" in token or "[CLS]" in token:
            continue
        else:
            arr.append(token)
    
    clean_text = " ".join(arr)
    clean_text = remove_special_characters(clean_text)
    result = generate_message(clean_text)
    if isinstance(result, tuple):
        text_final = result[0]
    else:
        text_final = result
    
    print(text_final)
    
    output_file_path = "output_text.txt"
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(text_final)
    
    return text_final 

def preprocess_text(text):
    text = remove_stop_words(text)
    text = remove_special_characters(text)
    return text

def build_faiss_index(folder_path, model_name='distilbert-base-uncased'):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    d = 768  
    index = faiss.IndexFlatL2(d)
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.pdf'):
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing {file_path}")
            text = extract_text_from_pdf(file_path)
            text = preprocess_text(text)
            embeddings = generate_embeddings(text, model, tokenizer)
            index.add(embeddings)
    
    return index
#folder_path = 'path/to/your/pdf/folder'
#index = build_faiss_index(folder_path)
#faiss.write_index(index, 'faiss_index.index')
#print("FAISS index saved successfully.")
