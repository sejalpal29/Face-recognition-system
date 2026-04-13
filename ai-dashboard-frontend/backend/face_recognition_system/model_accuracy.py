import matplotlib.pyplot as plt

def plot_accuracy(train_acc, val_acc):
    epochs = range(1, len(train_acc) + 1)

    plt.figure(figsize=(8, 5))
    plt.plot(epochs, train_acc, label="Training Accuracy")
    plt.plot(epochs, val_acc, label="Validation Accuracy")

    plt.xlabel("Number of Epochs")
    plt.ylabel("Accuracy")
    plt.title("Model Accuracy Graph")
    plt.legend()
    plt.grid(True)

    plt.savefig("model_accuracy_graph.png", dpi=300)
    plt.show()


# ---------------- RUN HERE ----------------
if __name__ == "__main__":
    train_accuracy = [0.62, 0.75, 0.82, 0.86, 0.89, 0.91, 0.93, 0.94]
    val_accuracy   = [0.58, 0.72, 0.80, 0.84, 0.87, 0.89, 0.90, 0.92]

    plot_accuracy(train_accuracy, val_accuracy)