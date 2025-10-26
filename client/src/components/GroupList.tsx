import { GroupSummary } from "../types";

interface GroupListProps {
  groups: GroupSummary[];
  selectedGroupId?: string;
  onSelect: (groupId: string) => void;
  onCreate: () => void;
  onJoin: () => void;
}

export function GroupList({
  groups,
  selectedGroupId,
  onSelect,
  onCreate,
  onJoin,
}: GroupListProps) {
  return (
    <div className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Groups</h2>
        <div className="space-x-2">
          <button
            type="button"
            onClick={onCreate}
            className="rounded-lg border border-xrpl-blue/40 px-3 py-1 text-sm font-medium text-xrpl-blue hover:bg-xrpl-blue/10"
          >
            Create
          </button>
          <button
            type="button"
            onClick={onJoin}
            className="rounded-lg border border-slate-700 px-3 py-1 text-sm font-medium text-slate-200 hover:bg-slate-800"
          >
            Join
          </button>
        </div>
      </div>

      <ul className="space-y-3">
        {groups.map((group) => {
          const isActive = group.id === selectedGroupId;
          return (
            <li key={group.id}>
              <button
                type="button"
                onClick={() => onSelect(group.id)}
                className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                  isActive
                    ? "border-xrpl-blue bg-xrpl-blue/10"
                    : "border-slate-800 hover:border-slate-700 hover:bg-slate-800/50"
                }`}
              >
                <p className="text-sm text-slate-400">{group.id}</p>
                <p className="text-lg font-semibold">{group.name}</p>
                <div className="mt-2 flex justify-between text-xs text-slate-500">
                  <span>{group.members} members</span>
                  <span>{group.totalLocked.toFixed(2)} XRP locked</span>
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
