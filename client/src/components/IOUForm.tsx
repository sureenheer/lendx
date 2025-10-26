import { FormEvent, useEffect, useMemo, useState } from "react";
import { IOURequest, Member } from "../types";

interface IOUFormProps {
  members: Member[];
  currentUser?: string;
  onSubmit: (request: IOURequest) => void;
}

export function IOUForm({ members, currentUser, onSubmit }: IOUFormProps) {
  const [debtor, setDebtor] = useState(currentUser ?? members[0]?.address ?? "");
  const [creditor, setCreditor] = useState(
    members.find((m) => m.address !== debtor)?.address ?? "",
  );
  const [amount, setAmount] = useState("0.00");

  const selectableMembers = useMemo(
    () => members.filter((member) => member.address !== debtor),
    [members, debtor],
  );

  useEffect(() => {
    if (!selectableMembers.find((member) => member.address === creditor)) {
      setCreditor(selectableMembers[0]?.address ?? "");
    }
  }, [selectableMembers, creditor]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const value = parseFloat(amount);
    if (!debtor || !creditor || Number.isNaN(value) || value <= 0) return;
    onSubmit({ debtor, creditor, amount: value });
    setAmount("0.00");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Add IOU</h3>
        <span className="text-xs text-slate-500">Balances update automatically</span>
      </div>

      <label className="block text-sm text-slate-400">
        Debtor
        <select
          value={debtor}
          onChange={(event) => setDebtor(event.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/50 px-3 py-2 text-white focus:border-xrpl-blue focus:outline-none"
        >
          {members.map((member) => (
            <option key={member.address} value={member.address}>
              {member.displayName ?? member.address}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm text-slate-400">
        Creditor
        <select
          value={creditor}
          onChange={(event) => setCreditor(event.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/50 px-3 py-2 text-white focus:border-xrpl-blue focus:outline-none"
        >
          {selectableMembers.map((member) => (
            <option key={member.address} value={member.address}>
              {member.displayName ?? member.address}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm text-slate-400">
        Amount (XRP)
        <input
          type="number"
          min="0"
          step="0.01"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/50 px-3 py-2 text-white focus:border-xrpl-blue focus:outline-none"
        />
      </label>

      <button
        type="submit"
        className="w-full rounded-lg bg-xrpl-blue px-4 py-2 font-medium text-white transition hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-xrpl-blue"
      >
        Submit IOU
      </button>
    </form>
  );
}
