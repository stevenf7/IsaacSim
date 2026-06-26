# Public API for module isaacsim.zmq.core:

## Classes

- class ZmqPublishSocket
  - def __init__(ip: str, port: int) -> None
  - def send_multipart(topic: str, payload: bytes) -> bool
  - [property] def ip() -> str
  - [property] def port() -> int

- class ZmqSubscribeSocket
  - def __init__(ip: str, port: int, topic: str) -> None
  - def try_recv() -> bytes | None
  - [property] def ip() -> str
  - [property] def port() -> int
  - [property] def topic() -> str
