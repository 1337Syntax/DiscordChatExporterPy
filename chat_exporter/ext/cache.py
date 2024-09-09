from functools import wraps

from typing import Any, Awaitable, Callable, Dict, Tuple, TypeVar

F = TypeVar('F', bound=Callable[..., Awaitable[Any]])


_internal_cache: Dict[str, Any] = {}


def _wrap_and_store_coroutine(cache: Dict[str, Any], key: str, coro: Awaitable[Any]) -> Awaitable[Any]:
    async def func() -> Any:
        value = await coro
        cache[key] = value
        return value
    return func()


def _wrap_new_coroutine(value: Any) -> Awaitable[Any]:
    async def new_coroutine() -> Any:
        return value
    return new_coroutine()


def clear_cache() -> None:
    _internal_cache.clear()


def cache() -> Callable[[F], F]:
    """Caches the Result of a Coroutine Function"""

    def decorator(func: F) -> F:
        def _make_key(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
            def _true_repr(o: Any) -> str:
                if o.__class__.__repr__ is object.__repr__:
                    return f'<{o.__class__.__module__}.{o.__class__.__name__}>'
                return repr(o)

            key = [f'{func.__module__}.{func.__name__}']
            key.extend(_true_repr(o) for o in args)
            for k, v in kwargs.items():
                key.append(_true_repr(k))
                key.append(_true_repr(v))

            return ':'.join(key)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Awaitable[Any]:
            key = _make_key(args, kwargs)
            try:
                value = _internal_cache[key]
            except KeyError:
                value = func(*args, **kwargs)
                return _wrap_and_store_coroutine(_internal_cache, key, value)
            else:
                return _wrap_new_coroutine(value)

        wrapper.cache = _internal_cache  # type: ignore
        wrapper.clear_cache = _internal_cache.clear  # type: ignore
        return wrapper  # type: ignore
    return decorator
