import multiprocessing as mp
import sys
import torch
from torch.utils.data import DataLoader, TensorDataset


def worker(q):
    q.put("child-ok")


if __name__ == "__main__":
    print("start_method", mp.get_start_method())
    q = mp.Queue()
    p = mp.Process(target=worker, args=(q,))
    p.start(); p.join()
    print("MP_PROCESS", p.exitcode, q.get())
    ds = TensorDataset(torch.zeros(8, 3, 8, 8), torch.zeros(8, 1, 8, 8))
    dl = DataLoader(ds, batch_size=2, num_workers=2)
    batches = len(list(dl))
    print("DATALOADER_WORKERS_2", batches)
    print("EXECUTABLE", sys.executable)
