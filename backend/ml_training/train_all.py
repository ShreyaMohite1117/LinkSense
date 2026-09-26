"""python -m ml_training.train_all"""
from ml_training import train_forecaster, train_phishing

if __name__ == "__main__":
    print("== Phishing classifier ==")
    train_phishing.train()
    print("\n== Click forecaster ==")
    train_forecaster.train()
