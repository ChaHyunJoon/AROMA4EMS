## Stable-Baseline3 concept memory buffer: ring buffer

import random
import numpy as np

class MemoryBuffer:
    def __init__(self, args):
        self.maxSize = int(args.buffer_size)
        self.batchSize = int(args.batch_size)
        # Default is without-replacement sampling (current behavior compatibility).
        # Can be switched globally or per random_sample() call.
        self.sample_with_replacement = bool(
            getattr(args, "buffer_sample_with_replacement", False)
        )

        # SB3-style ring buffer storage (preallocated numpy arrays).
        self._state = None
        self._action = None
        self._reward = None
        self._next_state = None
        self._done = None
        self._pos = 0
        self.currentSize = 0
        self.counter = 0

    @staticmethod
    def _to_array(x):
        arr = np.asarray(x, dtype=np.float32)
        if arr.ndim == 0:
            arr = np.expand_dims(arr, axis=0)
        return arr

    def _init_storage(self, s, a):
        self._state = np.empty((self.maxSize, *s.shape), dtype=np.float32)
        self._action = np.empty((self.maxSize, *a.shape), dtype=np.float32)
        self._reward = np.empty((self.maxSize,), dtype=np.float32)
        self._next_state = np.empty((self.maxSize, *s.shape), dtype=np.float32)
        self._done = np.empty((self.maxSize,), dtype=np.float32)

    def store(self, s, a, r, s_, done=None):
        s_arr = self._to_array(s)
        a_arr = self._to_array(a)
        s_next_arr = self._to_array(s_)
        if self._state is None:
            self._init_storage(s_arr, a_arr)

        self._state[self._pos] = s_arr
        self._action[self._pos] = a_arr
        self._reward[self._pos] = np.float32(r)
        self._next_state[self._pos] = s_next_arr
        self._done[self._pos] = float(bool(done))

        self._pos = (self._pos + 1) % self.maxSize
        self.counter += 1
        self.currentSize = min(self.counter, self.maxSize)

    def _sample_indices(self, replace):
        if self.currentSize <= 0:
            raise ValueError("Cannot sample from an empty buffer.")
        if replace:
            return np.random.randint(0, self.currentSize, size=self.batchSize)
        if self.batchSize > self.currentSize:
            # Keep parity with random.sample failure condition.
            raise ValueError("Sample larger than population or is negative")
        return np.fromiter(
            random.sample(range(self.currentSize), self.batchSize),
            dtype=np.int64,
            count=self.batchSize,
        )

    def random_sample(self, replace=None):
        use_replace = self.sample_with_replacement if replace is None else bool(replace)
        idx = self._sample_indices(use_replace)
        s = self._state[idx]
        a = self._action[idx]
        r = self._reward[idx]
        s_ = self._next_state[idx]
        return (s, a, r, s_, self._done[idx])
    


class SumTree:
    """비재귀 numpy sum-tree. batch 단위 갱신/샘플링을 고정 깊이 루프로 벡터화한다.

    tree[1] 이 루트, leaf i 는 tree[capacity + i]. capacity 는 2의 거듭제곱.
    """

    def __init__(self, capacity):
        cap = 1
        while cap < int(capacity):
            cap <<= 1
        self.capacity = cap
        self.depth = int(np.log2(cap))
        self.tree = np.zeros(2 * cap, dtype=np.float64)

    @property
    def total(self):
        return float(self.tree[1])

    def update(self, idxs, values):
        idxs = np.asarray(idxs, dtype=np.int64).reshape(-1)
        values = np.asarray(values, dtype=np.float64).reshape(-1)
        # 같은 인덱스가 배치 안에 두 번 오면 delta 가 중복 계산되므로 마지막 값만 남긴다.
        if idxs.size > 1:
            order = np.arange(idxs.size)
            uniq, last = np.unique(idxs[::-1], return_index=True)
            keep = order.size - 1 - last
            idxs, values = idxs[keep], values[keep]
        leaf = idxs + self.capacity
        delta = values - self.tree[leaf]
        self.tree[leaf] = values
        for d in range(1, self.depth + 1):
            np.add.at(self.tree, leaf >> d, delta)

    def sample(self, n, rng=None):
        """stratified sampling: [0, total) 를 n등분해 구간마다 하나씩 뽑는다."""
        rng = np.random if rng is None else rng
        total = self.total
        seg = total / n
        u = (np.arange(n) + rng.random_sample(n)) * seg
        idx = np.ones(n, dtype=np.int64)
        for _ in range(self.depth):
            left = idx << 1
            left_sum = self.tree[left]
            go_right = u > left_sum
            u = np.where(go_right, u - left_sum, u)
            idx = left + go_right.astype(np.int64)
        leaf = idx - self.capacity
        return np.clip(leaf, 0, self.capacity - 1), self.tree[idx]


class PrioritizedMemoryBuffer(MemoryBuffer):
    """Proportional PER (Schaul et al., ICLR 2016).

    p_i = (|TD_i| + eps)^alpha,  P(i) = p_i / sum_j p_j
    IS weight w_i = (N * P(i))^(-beta) / max_k w_k   (beta 는 1.0 까지 annealing)

    새로 들어온 transition 은 지금까지의 최대 우선순위를 받아 최소 1회는 뽑히게 한다.
    """

    def __init__(self, args):
        super().__init__(args)
        self.per_alpha = float(getattr(args, "per_alpha", 0.6))
        self.per_beta0 = float(getattr(args, "per_beta0", 0.4))
        self.per_beta_steps = int(getattr(args, "per_beta_steps", 0) or 0)
        self.per_eps = float(getattr(args, "per_eps", 1e-6))
        self._tree = SumTree(self.maxSize)
        self._max_priority = 1.0
        self._beta_step = 0

    def store(self, s, a, r, s_, done=None):
        pos = self._pos
        super().store(s, a, r, s_, done)
        # 새 transition 은 최대 우선순위로 -> 한 번은 반드시 학습에 쓰인다
        self._tree.update(np.array([pos]), np.array([self._max_priority]))

    def current_beta(self):
        if self.per_beta_steps <= 0:
            return 1.0
        frac = min(1.0, self._beta_step / float(self.per_beta_steps))
        return self.per_beta0 + frac * (1.0 - self.per_beta0)

    def sample_prioritized(self):
        beta = self.current_beta()
        self._beta_step += 1
        idx, prio = self._tree.sample(self.batchSize)
        total = self._tree.total
        n = max(1, self.currentSize)
        probs = np.maximum(prio, 1e-12) / max(total, 1e-12)
        weights = (n * probs) ** (-beta)
        weights = weights / weights.max()
        batch = (self._state[idx], self._action[idx], self._reward[idx], self._next_state[idx], self._done[idx])
        return batch, idx, weights.astype(np.float32), beta

    def update_priorities(self, idx, abs_td):
        p = (np.abs(np.asarray(abs_td, dtype=np.float64)).reshape(-1) + self.per_eps) ** self.per_alpha
        self._max_priority = max(self._max_priority, float(p.max()))
        self._tree.update(idx, p)


def make_buffer(args):
    """--per 여부에 따라 uniform / prioritized 버퍼를 만든다."""
    if bool(getattr(args, "per", False)):
        return PrioritizedMemoryBuffer(args)
    return MemoryBuffer(args)
