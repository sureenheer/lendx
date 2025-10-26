import { useEffect, useState } from "react";
import { fetchBalances, fetchGroup } from "../services/api";
import { GroupDetails } from "../types";

const POLL_INTERVAL_MS = 5_000;

export function useGroup(groupId?: string) {
  const [group, setGroup] = useState<GroupDetails | null>(null);
  const [balances, setBalances] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!groupId) {
      setGroup(null);
      setBalances({});
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        const data = await fetchGroup(groupId);
        if (!cancelled) {
          setGroup(data as unknown as GroupDetails);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [groupId]);

  useEffect(() => {
    if (!groupId) return;
    let cancelled = false;

    async function poll() {
      try {
        const data = await fetchBalances(groupId);
        if (!cancelled) {
          setBalances(data);
        }
      } catch (err) {
        if (!cancelled) {
          console.warn("Failed to fetch balances", err);
        }
      }
    }

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [groupId]);

  return { group, balances, loading, error };
}
