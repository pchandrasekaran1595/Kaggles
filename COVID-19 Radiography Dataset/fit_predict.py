import torch
import numpy as np
from time import time
from sklearn.metrics import accuracy_score

def breaker():
    print("\n" + 50 * "-" + "\n")

def fit_(model=None, optimizer=None, scheduler=None, epochs=None, early_stopping_patience=None,
         trainloader=None, validloader=None, criterion=None, device=None, verbose=False, path=None):
    breaker()
    print("Training ...")
    breaker()

    if device:
        model.to(device)

    Losses = []
    Accuracies = []

    DLS = {"train": trainloader, "valid": validloader}
    bestLoss = {"train": np.inf, "valid": np.inf}
    bestAccs = {"train": 0.0, "valid": 0.0}

    start_time = time()
    for e in range(epochs):
        e_st = time()

        epochLoss = {"train": 0.0, "valid": 0.0}
        epochAccs = {"train": 0.0, "valid": 0.0}

        for phase in ["train", "valid"]:
            if phase == "train":
                model.train()
            else:
                model.eval()

            lossPerPass = []
            accsPerPass = []

            for X, y in DLS[phase]:
                X, y = X.to(device), y.to(device).view(-1)

                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == "train"):
                    output = model(X)
                    loss = criterion(output, y)
                    if phase == "train":
                        loss.backward()
                        optimizer.step()
                lossPerPass.append(loss.item())
                accsPerPass.append(accuracy_score(torch.argmax(torch.exp(output), dim=1).detach().cpu().numpy(),
                                                  y.detach().cpu().numpy()))
            epochLoss[phase] = np.mean(np.array(lossPerPass))
            epochAccs[phase] = np.mean(np.array(accsPerPass))
        Losses.append(epochLoss)
        Accuracies.append(epochAccs)

        """if early_stopping_patience:
            if epochLoss["valid"] < bestLoss["valid"]: # or epochAccs["valid"] > bestAccs["valid"]:
                bestLoss = epochLoss
                early_stopping_step = 0
                bestEpoch = e+1
            else:
                early_stopping_step += 1
                if early_stopping_step > early_stopping_patience:
                    print("Early Stopping at Epoch {}".format(bestEpoch))"""

        torch.save({"model_state_dict": model.state_dict(),
                    "optim_state_dict": optimizer.state_dict()},
                   "./Epoch_{}.pt".format(e + 1))

        if epochLoss["valid"] < bestLoss["valid"]:
            bestLoss = epochLoss
            bestLossEpoch = e + 1

        if epochAccs["valid"] > bestAccs["valid"]:
            bestAccs = epochAccs
            bestAccsEpoch = e + 1

        if scheduler:
            # scheduler.step()
            scheduler.step(epochLoss["valid"])

        if verbose:
            print("Epoch: {} | Train Loss: {:.5f} | Valid Loss: {:.5f} | \
Train Accuracy: {:.5f} | Valid Accuracy: {:.5f} | Time: {:.2f} seconds".format(e + 1, epochLoss["train"],
                                                                               epochLoss["valid"],
                                                                               epochAccs["train"], epochAccs["valid"],
                                                                               time() - e_st))

    breaker()
    print("-----> Best Validation Loss at Epoch {}".format(bestLossEpoch))
    breaker()
    print("-----> Best Validation Accs at Epoch {}".format(bestAccsEpoch))
    breaker()
    print("Time Taken [{} Epochs] : {:.2f} minutes".format(epochs, (time() - start_time) / 60))
    breaker()
    print("Training Complete")
    breaker()

    return Losses, Accuracies, bestLossEpoch, bestAccsEpoch


def predict_(model=None, dataloader=None, device=None, path=None):
    if path:
        model.load_state_dict(torch.load(path)["model_state_dict"])

    model.to(device)
    model.eval()

    y_pred = torch.zeros(1, 1).to(device)

    for X, y in dataloader:
        X = X.to(device)
        with torch.no_grad():
            output = torch.argmax(torch.exp(model(X)), dim=1)
        y_pred = torch.cat((y_pred, output), dim=0)

    return y_pred[1:].detach().cpu().numpy().astype(int)