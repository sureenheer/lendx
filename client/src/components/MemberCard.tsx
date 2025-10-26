import { Member } from "../types";

const colorMap = {
  positive: "text-emerald-400",
  negative: "text-rose-400",
  neutral: "text-slate-400",
};

function formatAddress(address: string) {
  if (address.length <= 10) return address;
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

function formatNet(amount: number) {
  return `${amount > 0 ? "+" : ""}${amount.toFixed(2)} XRP`;
}

interface MemberCardProps {
  member: Member;
}

export function MemberCard({ member }: MemberCardProps) {
  const tone =
    member.netBalance > 0
      ? colorMap.positive
      : member.netBalance < 0
        ? colorMap.negative
        : colorMap.neutral;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-lg shadow-black/30">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{member.displayName ?? "Member"}</p>
          <p className="text-lg font-semibold">{formatAddress(member.address)}</p>
        </div>
        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-xs uppercase tracking-wide text-slate-300">
          DID
        </span>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <div>
          <p className="text-xs uppercase text-slate-500">Net Balance</p>
          <p className={`text-xl font-bold ${tone}`}>{formatNet(member.netBalance)}</p>
        </div>
        <span className="text-xs text-slate-500">Status: {member.status}</span>
      </div>

      <div className="mt-4 text-xs text-slate-500">
        Last active <span className="text-slate-300">{member.lastActive}</span>
      </div>
    </div>
  );
}
