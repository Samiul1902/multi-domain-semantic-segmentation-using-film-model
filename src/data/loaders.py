import torch
from torch.utils.data import DataLoader
from src.utils.reproducibility import make_generator, seed_worker


def create_loader(dataset, batch_size, shuffle, seed=42, num_workers=0,
                  pin_memory=True, persistent_workers=False, generator_state=None):
    if getattr(dataset,"split","").upper()=="TEST":
        raise RuntimeError("Development loaders reject TEST data")
    generator = make_generator(seed)
    if generator_state is not None:
        generator.set_state(generator_state.detach().to(device="cpu", dtype=torch.uint8))
    return DataLoader(dataset,batch_size=batch_size,shuffle=shuffle,num_workers=num_workers,
                      pin_memory=pin_memory,persistent_workers=persistent_workers and num_workers>0,
                      worker_init_fn=seed_worker,generator=generator)
