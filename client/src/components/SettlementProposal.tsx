import { SettlementProposalData } from "../types";

interface SettlementProposalProps {
  proposal: SettlementProposalData;
  onSign: () => Promise<void> | void;
  onBroadcast: () => Promise<void> | void;
}

function statusClass(status: string) {
  const base = "px-3 py-1 rounded-full text-xs font-semibold capitalize";
  switch (status) {
    case "pending":
    case "pending_signatures":
      return `${base} bg-amber-400/20 text-amber-300 border border-amber-400/40`;
    case "ready_to_broadcast":
    case "broadcast":
      return `${base} bg-blue-400/20 text-blue-200 border border-blue-500/40`;
    case "completed":
      return `${base} bg-emerald-400/20 text-emerald-200 border border-emerald-400/40`;
    default:
      return `${base} bg-slate-700/40 text-slate-200 border border-slate-600/60`;
  }
}

export function SettlementProposal({
  proposal,
  onSign,
  onBroadcast,
}: SettlementProposalProps) {
  const progress = Math.min(
    100,
    (proposal.collectedSignatures / proposal.requiredSignatures) * 100,
  );

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-500">Settlement Proposal</p>
          <h2 className="text-2xl font-bold">{proposal.id.slice(0, 8)}…</h2>
        </div>
        <span className={statusClass(proposal.status)}>{proposal.status.replace("_", " ")}</span>
      </div>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr className="border-b border-slate-800">
              <th className="py-2">From</th>
              <th className="py-2">To</th>
              <th className="py-2 text-right">Amount (XRP)</th>
            </tr>
          </thead>
          <tbody>
            {proposal.payments.map((payment) => (
              <tr key={`${payment.from}-${payment.to}`} className="border-b border-slate-800/60">
                <td className="py-2">{payment.from}</td>
                <td className="py-2">{payment.to}</td>
                <td className="py-2 text-right font-semibold text-slate-100">
                  {payment.amount.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-4">
          <div
            className="h-20 w-20 rounded-full border-4 border-slate-800"
            style={{
              background: `conic-gradient(#00e09d ${progress}%, rgba(15,23,42,0.9) ${progress}% 100%)`,
            }}
          >
            <div className="flex h-full w-full items-center justify-center rounded-full bg-slate-950">
              <div className="text-center">
                <p className="text-xl font-bold text-white">{proposal.collectedSignatures}</p>
                <p className="text-xs text-slate-400">of {proposal.requiredSignatures}</p>
              </div>
            </div>
          </div>
          <div>
            <p className="text-sm text-slate-400">Signature progress</p>
            <p className="text-lg font-semibold">Xaman multisig workflow</p>
          </div>
        </div>

        <div className="ml-auto flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onSign}
            className="rounded-full bg-xrpl-blue px-6 py-2 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Sign via Xaman
          </button>
          <button
            type="button"
            onClick={onBroadcast}
            className="rounded-full border border-slate-700 px-6 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={proposal.status !== "ready_to_broadcast"}
          >
            Broadcast escrow set
          </button>
        </div>
      </div>
    </div>
  );
}
