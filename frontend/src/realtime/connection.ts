export interface ConnectionCallbacks {
  message: (data: unknown) => void;
  status: (online: boolean) => void;
  expired: () => void;
}
export function createConnection(callbacks: ConnectionCallbacks) {
  let socket: WebSocket | undefined,
    retry: ReturnType<typeof setTimeout> | undefined,
    beat: ReturnType<typeof setInterval> | undefined;
  let closed = true,
    attempts = 0,
    lastMessage = 0,
    resyncAt = 0;
  function resync() {
    if (socket?.readyState === WebSocket.OPEN && Date.now() - resyncAt > 1000) {
      resyncAt = Date.now();
      socket.send("resync");
    }
  }
  function open() {
    if (
      closed ||
      (socket &&
        (socket.readyState === WebSocket.CONNECTING ||
          socket.readyState === WebSocket.OPEN))
    )
      return;
    const current = new WebSocket(
      `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/ws?protocol=2`,
    );
    socket = current;
    current.onopen = () => {
      if (socket !== current) return;
      lastMessage = Date.now();
      callbacks.status(true);
      clearInterval(beat);
      beat = setInterval(() => {
        if (Date.now() - lastMessage > 18000) {
          current.close();
          return;
        }
        if (current.readyState === WebSocket.OPEN) current.send("ping");
      }, 5000);
    };
    current.onmessage = (e) => {
      if (socket !== current || closed) return;
      lastMessage = Date.now();
      try {
        const data = JSON.parse(e.data);
        callbacks.message(data);
        attempts = 0;
      } catch {
        resync();
      }
    };
    current.onclose = (e) => {
      if (socket !== current) return;
      socket = undefined;
      clearInterval(beat);
      callbacks.status(false);
      if (closed) return;
      if (e.code === 4401 || e.code === 4001) {
        closed = true;
        callbacks.expired();
        return;
      }
      const delay =
        Math.min(30000, 750 * 2 ** Math.min(attempts++, 6)) *
        (0.8 + Math.random() * 0.4);
      retry = setTimeout(open, delay);
    };
    current.onerror = () => callbacks.status(false);
  }
  function stop() {
    closed = true;
    clearTimeout(retry);
    clearInterval(beat);
    const old = socket;
    socket = undefined;
    old?.close();
    callbacks.status(false);
  }
  return {
    start() {
      if (!closed) return;
      closed = false;
      attempts = 0;
      open();
    },
    stop,
    resync,
  };
}
