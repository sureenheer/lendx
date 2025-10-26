import { useCallback, useEffect, useState } from "react";
import {
  broadcastSettlement,
  fetchSettlement,
  signSettlement,
} from "../services/api";
import { SettlementProposalData } from "../types";

type Status = "idle" | "loading" | "signing" | "broadcasting" | "error";

export function useSettlement(groupId?: string) {
  const [proposal, setProposal] = useState<SettlementProposalData | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!groupId) {
      setProposal(null);
      return;
    }

    let cancelled = false;

    async function load() {
      setStatus("loading");
      try {
        const data = await fetchSettlement(groupId);
        if (!cancelled) {
          setProposal(data as SettlementProposalData);
          setStatus("idle");
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setStatus("error");
          setError((err as Error).message);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [groupId]);

  const sign = useCallback(
    async (proposalId?: string) => {
      if (!proposalId && !proposal) throw new Error("No proposal to sign");
      const id = proposalId ?? proposal!.id;
      setStatus("signing");
      try {
        const data = await signSettlement(id);
        setProposal(data as SettlementProposalData);
        setStatus("idle");
      } catch (err) {
        setStatus("error");
        setError((err as Error).message);
        throw err;
      }
    },
    [proposal],
  );

  const broadcast = useCallback(
    async (proposalId?: string) => {
      if (!proposalId && !proposal) throw new Error("No proposal to broadcast");
      const id = proposalId ?? proposal!.id;
      setStatus("broadcasting");
      try {
        const data = await broadcastSettlement(id);
        setProposal(data as SettlementProposalData);
        setStatus("idle");
      } catch (err) {
        setStatus("error");
        setError((err as Error).message);
        throw err;
      }
    },
    [proposal],
  );

  return {
    proposal,
    sign,
    broadcast,
    status,
    error,
  };
}
