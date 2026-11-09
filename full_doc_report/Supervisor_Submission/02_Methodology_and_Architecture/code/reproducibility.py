import random
import numpy as np
import torch


def set_seed(seed, deterministic=True):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = deterministic
    torch.backends.cudnn.benchmark = not deterministic


def seed_worker(worker_id):
    seed = torch.initial_seed() % (2**32)
    random.seed(seed); np.random.seed(seed)


def make_generator(seed):
    generator=torch.Generator(); generator.manual_seed(seed); return generator


def capture_random_state():
    state={"python":random.getstate(),"numpy":np.random.get_state(),"torch_cpu":torch.get_rng_state()}
    if torch.cuda.is_available(): state["torch_cuda"]=torch.cuda.get_rng_state_all()
    return state


def restore_random_state(state):
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    cpu_state = state["torch_cpu"].detach().to(device="cpu", dtype=torch.uint8)
    torch.set_rng_state(cpu_state)
    if torch.cuda.is_available() and "torch_cuda" in state:
        cuda_states = [value.detach().to(device="cpu", dtype=torch.uint8) for value in state["torch_cuda"]]
        torch.cuda.set_rng_state_all(cuda_states)
