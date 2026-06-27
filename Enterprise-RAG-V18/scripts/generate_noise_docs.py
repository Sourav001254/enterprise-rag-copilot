import os
import random

def generate_noise():
    output_dir = "data/raw/noise"
    os.makedirs(output_dir, exist_ok=True)
    
    topics = ["Cooking Recipes", "Car Maintenance", "History of Rome", "Quantum Physics", "Gardening Tips"]
    
    for i in range(10):
        topic = random.choice(topics)
        with open(os.path.join(output_dir, f"noise_{i}.txt"), "w") as f:
            f.write(f"This document is about {topic}. It has nothing to do with Kubernetes or IT operations. " * 50)
            
    print(f"Generated 10 noise documents in {output_dir}")

if __name__ == "__main__":
    generate_noise()
