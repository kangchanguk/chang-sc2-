import pickle
import pickletools
import os

import joblib
import numpy as np


class BasePickler:
    def encode(self, obj):
        raise NotImplementedError

    def decode(self, dumped):
        raise NotImplementedError


class BasicPicker(BasePickler):
    def encode(self, obj):
        return pickle.dumps(obj, protocol=2)

    def decode(self, dumped):
        return pickle.loads(dumped)


class OptimizedPicker(BasePickler):
    def encode(self, obj):
        # 불필요한 put op 제거하여 용량 축소 및 로드 속도 향상
        # 자기참조를 가진 객체를 처리 못함
        # loads 할 때는 BASIC과 동일
        pickled = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        identical = pickletools.optimize(pickled)
        return identical

    def decode(self, dumped):
        return pickle.loads(dumped)


class PickleArray:
    def __init__(self, directory, shape, pickler_cls):
        self.directory = Path(directory)
        self.shape = shape
        self.pickler = pickler_cls()
        self.max_dump_size = 0

        self.path = self.directory / f'{self.shape[1]}.mem'
        mode = 'r+' if self.path.exists() else 'w+'
        self.mem = np.memmap(self.path, dtype=f'S{shape[1]}', mode=mode, shape=shape[0])
        
    def __repr__(self):
        buff = f'path: {self.directory}\n'
        buff += f'shape: {self.shape}\n'
        buff += f'pickler: {self.pickler.__class__.__name__}\n'
        return buff

    def __setitem__(self, idx, obj):
        encoded_obj = self.pickler.encode(obj)
        self.max_dump_size = max(self.max_dump_size, len(encoded_obj))
        if len(encoded_obj) > self.shape[1]:
            self.expand()
        self.mem[idx] = encoded_obj

    def __getitem__(self, idx):
        return self.pickler.decode(self.mem[idx])

    def expand(self):
        new_shape = (self.shape[0], 2 * self.shape[1])
        new_path = self.directory / f'{new_shape[1]}.mem'
        new_mem = np.memmap(new_path, dtype=f'S{new_shape[1]}', mode='w+', shape=new_shape[0])
        new_mem[:] = self.mem

        self.mem._mmap.close()
        self.path.unlink()

        self.shape = new_shape
        self.path = new_path
        self.mem = new_mem




if __name__ == '__main__':

    import tempfile
    from IPython import embed
    from pathlib import Path

    tmpfile = Path(tempfile.mkdtemp())
    print(tmpfile)

    buffer = PickleArray(tmpfile, shape=(100, 1000), pickler_cls=OptimizedPicker)

    for i in range(100):
        xs = np.random.random((i, i))
        buffer[i] = xs
        print(i, (buffer[i] == xs).all())
    embed()
