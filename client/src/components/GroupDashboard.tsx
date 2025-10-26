import { IOUForm } from "./IOUForm";
import { MemberCard } from "./MemberCard";
import { GroupDetails, IOURequest } from "../types";

interface GroupDashboardProps {
  group: GroupDetails;
  currentUser?: string;
  onAddIou: (request: IOURequest) => void;
  onProposeSettlement: () => void;
  children?: React.ReactNode;
}

function formatAddress(address: string) {
  if (address.length <= 12) return address;
  return `${address.slice(0, 8)}…${address.slice(-6)}`;
}

export function GroupDashboard({
  group,
  currentUser,
  onAddIou,
  onProposeSettlement,
  children,
}: GroupDashboardProps) {
  return (
    <div className="space-y-6">
      <header className="rounded-3xl border border-slate-800 bg-gradient-to-r from-slate-900 to-slate-950 p-6 shadow-lg shadow-black/30">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-slate-400">Group</p>
            <h1 className="text-3xl font-bold tracking-tight">{group.name}</h1>
          </div>
          <button
            type="button"
            onClick={onProposeSettlement}
            className="rounded-full bg-xrpl-green px-6 py-2 text-sm font-semibold text-black shadow-lg shadow-emerald-500/40 transition hover:bg-emerald-400"
          >
            Propose Settlement
          </button>
        </div>

        <div className="mt-6 grid gap-4 text-sm text-slate-300 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-800/60 bg-slate-900/40 p-4">
            <p className="text-xs uppercase text-slate-500">Deposit Account</p>
            <p className="text-lg font-semibold">{formatAddress(group.depositAccount)}</p>
          </div>
          <div className="rounded-2xl border border-slate-800/60 bg-slate-900/40 p-4">
            <p className="text-xs uppercase text-slate-500">Members</p>
            <p className="text-lg font-semibold">{group.members}</p>
          </div>
          <div className="rounded-2xl border border-slate-800/60 bg-slate-900/40 p-4">
            <p className="text-xs uppercase text-slate-500">Locked XRP</p>
            <p className="text-lg font-semibold">{group.totalLocked.toFixed(2)} XRP</p>
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {group.memberDetails.map((member) => (
              <MemberCard key={member.address} member={member} />
            ))}
          </div>
          {children}
        </div>
        <IOUForm members={group.memberDetails} currentUser={currentUser} onSubmit={onAddIou} />
      </section>
    </div>
  );
}
