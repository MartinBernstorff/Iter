import multiprocessing
from collections import defaultdict
from collections.abc import (
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from copy import deepcopy
from functools import reduce
from itertools import islice
from typing import Generic, TypeVar

T = TypeVar("T")
S = TypeVar("S")


class Seq(Generic[T]):
    def __init__(self, iterable: Iterable[T]) -> None:
        self._iterator: Iterator[T] = iter(iterable)

    @property
    def _non_consumable(self) -> Iterator[T]:
        return deepcopy(self._iterator)

    def __getitem__(self, index: int | slice) -> T | "Seq[T]":
        if isinstance(index, int) and index >= 0:
            try:
                return list(self._non_consumable)[index]
            except StopIteration:
                raise IndexError("Index out of range") from None
        elif isinstance(index, slice):
            return Seq(
                islice(
                    self._non_consumable,
                    index.start,
                    index.stop,
                    index.step,
                )
            )
        else:
            raise KeyError(
                f"Key must be non-negative integer or slice, not {index}"
            )

    ### Reductions
    def count(self) -> int:
        return sum(1 for _ in self._iterator)

    ### Output
    def to_list(self) -> list[T]:
        return list(self._iterator)

    def to_tuple(self) -> tuple[T, ...]:
        return tuple(self._iterator)  # pragma: no cover

    def to_iter(self) -> Iterator[T]:
        return iter(self._iterator)  # pragma: no cover

    def to_set(self) -> set[T]:
        return set(self._iterator)  # pragma: no cover

    ### Transformations
    def map(  # noqa: A003 # Ignore that it's shadowing a python built-in
        self,
        func: Callable[[T], S],
    ) -> "Seq[S]":
        return Seq(map(func, self._iterator))

    def pmap(
        self,
        func: Callable[[T], S],
    ) -> "Seq[S]":
        """Parallel map using multiprocessing.Pool

        Not that lambdas are not supported by multiprocessing.Pool.map.
        """
        with multiprocessing.Pool() as pool:
            return Seq(pool.map(func, self._iterator))

    def filter(self, func: Callable[[T], bool]) -> "Seq[T]":  # noqa: A003
        return Seq(filter(func, self._iterator))

    def reduce(self, func: Callable[[T, T], T]) -> T:
        return reduce(func, self._iterator)

    def groupby(
        self, func: Callable[[T], str]
    ) -> "Mapping[str, Sequence[T]]":
        mapping: defaultdict[str, list[T]] = defaultdict(list)

        for item in self._iterator:
            mapping[func(item)].append(item)

        return dict(mapping)

    def flatten(self) -> "Seq[T]":
        values: list[T] = []

        for i in self._iterator:
            if isinstance(i, Sequence):
                values.extend(i)
            else:
                values.append(i)

        return Seq(values)
