type BalanceHandler = (payload: { address: string; balance?: number; raw: unknown }) => void;

const XRPL_WS_URL =
  import.meta.env.VITE_XRPL_WS_URL ?? "wss://s.altnet.rippletest.net:51233";

let socket: WebSocket | null = null;
const subscriptions = new Map<string, Set<BalanceHandler>>();
const pendingAccounts = new Set<string>();

function ensureSocket() {
  if (socket && socket.readyState <= WebSocket.CONNECTING) {
    return;
  }

  socket = new WebSocket(XRPL_WS_URL);

  socket.addEventListener("open", () => {
    pendingAccounts.forEach((account) => subscribeAccount(account));
  });

  socket.addEventListener("message", (event) => {
    try {
      const data = JSON.parse(event.data);
      handleMessage(data);
    } catch (error) {
      console.warn("Failed to parse XRPL WS payload", error);
    }
  });

  socket.addEventListener("close", () => {
    setTimeout(() => {
      ensureSocket();
    }, 1_000);
  });
}

function subscribeAccount(account: string) {
  if (!socket) return;
  if (socket.readyState !== WebSocket.OPEN) {
    pendingAccounts.add(account);
    return;
  }

  socket.send(
    JSON.stringify({
      command: "subscribe",
      accounts: [account],
    }),
  );
}

function unsubscribeAccount(account: string) {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;
  socket.send(
    JSON.stringify({
      command: "unsubscribe",
      accounts: [account],
    }),
  );
}

function handleMessage(data: any) {
  if (data.type !== "transaction" || !data.validated) return;
  const affectedAccounts = new Set<string>();
  if (data.transaction?.Account) affectedAccounts.add(data.transaction.Account);
  if (data.transaction?.Destination) affectedAccounts.add(data.transaction.Destination);

  affectedAccounts.forEach((account) => {
    const handlers = subscriptions.get(account);
    if (!handlers) return;
    handlers.forEach((handler) =>
      handler({
        address: account,
        balance: parseDeliveredAmount(data.meta?.delivered_amount),
        raw: data,
      }),
    );
  });
}

function parseDeliveredAmount(amount: any) {
  if (typeof amount === "string") {
    return parseFloat(amount) / 1_000_000;
  }
  if (typeof amount === "number") {
    return amount / 1_000_000;
  }
  if (typeof amount === "object" && amount?.value) {
    return parseFloat(amount.value);
  }
  return undefined;
}

export function subscribeToBalance(account: string, handler: BalanceHandler) {
  ensureSocket();
  const handlers = subscriptions.get(account) ?? new Set<BalanceHandler>();
  handlers.add(handler);
  subscriptions.set(account, handlers);
  subscribeAccount(account);

  return () => {
    const current = subscriptions.get(account);
    if (!current) return;
    current.delete(handler);
    if (current.size === 0) {
      subscriptions.delete(account);
      unsubscribeAccount(account);
    }
  };
}
