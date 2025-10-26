import { useEffect, useMemo, useState } from "react";
import { GroupDashboard } from "./components/GroupDashboard";
import { GroupList } from "./components/GroupList";
import { SettlementProposal } from "./components/SettlementProposal";
import { useGroup } from "./hooks/useGroup";
import { useSettlement } from "./hooks/useSettlement";
import { useWallet } from "./hooks/useWallet";
import {
  GroupDetails,
  GroupSummary,
  IOURequest,
  Member,
  SettlementPayment,
  SettlementProposalData,
} from "./types";

const sampleMembers: Member[] = [
  {
    address: "rAlice12345abcdef67890",
    displayName: "Alice",
    netBalance: 50,
    lastActive: "5m ago",
    status: "pending",
  },
  {
    address: "rBob98765abcdef12345",
    displayName: "Bob",
    netBalance: -30,
    lastActive: "12m ago",
    status: "pending",
  },
  {
    address: "rCarol11111abcdef22222",
    displayName: "Carol",
    netBalance: -20,
    lastActive: "1h ago",
    status: "pending",
  },
];

const sampleGroups: GroupDetails[] = [
  {
    id: "grp-xrpl-devs",
    name: "XRPL Devs",
    members: sampleMembers.length,
    totalLocked: 120.5,
    depositAccount: "rGroupDeposit1111111111111",
    memberDetails: sampleMembers,
  },
];

export default function App() {
  const [groups] = useState<GroupSummary[]>(
    sampleGroups.map(({ id, name, members, totalLocked }) => ({
      id,
      name,
      members,
      totalLocked,
    })),
  );
  const [groupDetails, setGroupDetails] = useState<Record<string, GroupDetails>>(
    Object.fromEntries(sampleGroups.map((group) => [group.id, group])),
  );
  const [selectedGroupId, setSelectedGroupId] = useState(sampleGroups[0]?.id);
  const [localProposal, setLocalProposal] = useState<SettlementProposalData | null>(null);

  const group = selectedGroupId ? groupDetails[selectedGroupId] : undefined;
  const { group: remoteGroup, balances } = useGroup(selectedGroupId);
  const {
    proposal: remoteProposal,
    sign: signRemoteProposal,
    broadcast: broadcastRemoteProposal,
  } = useSettlement(selectedGroupId);
  const { address, loading: walletLoading, connect, sign } = useWallet();

  useEffect(() => {
    if (!remoteGroup) return;
    setGroupDetails((prev) => ({ ...prev, [remoteGroup.id]: remoteGroup }));
  }, [remoteGroup]);

  useEffect(() => {
    if (!group || !balances || Object.keys(balances).length === 0) return;
    setGroupDetails((prev) => {
      const current = prev[group.id];
      if (!current) return prev;
      const updatedMembers = current.memberDetails.map((member) =>
        balances[member.address] !== undefined
          ? { ...member, netBalance: balances[member.address] }
          : member,
      );
      return { ...prev, [group.id]: { ...current, memberDetails: updatedMembers } };
    });
  }, [balances, group]);

  const activeProposal = remoteProposal ?? localProposal;

  const handleAddIou = (request: IOURequest) => {
    if (!group) return;
    setGroupDetails((prev) => {
      const updated = { ...prev };
      const target = updated[group.id];
      const members = target.memberDetails.map((member) => {
        if (member.address === request.debtor) {
          return { ...member, netBalance: member.netBalance + request.amount };
        }
        if (member.address === request.creditor) {
          return { ...member, netBalance: member.netBalance - request.amount };
        }
        return member;
      });
      updated[group.id] = { ...target, memberDetails: members };
      return updated;
    });
  };

  const handleProposeSettlement = () => {
    if (!group) return;
    const payments = buildPayments(group.memberDetails);
    setLocalProposal({
      id: crypto.randomUUID(),
      payments,
      requiredSignatures: 2,
      collectedSignatures: 0,
      status: "pending_signatures",
    });
  };

  const handleSign = async () => {
    if (!activeProposal) return;
    await sign({
      TransactionType: "MultiSignature",
      ProposalID: activeProposal.id,
    });
    if (remoteProposal) {
      await signRemoteProposal(activeProposal.id);
      return;
    }
    setLocalProposal((prev) =>
      prev
        ? {
            ...prev,
            collectedSignatures: Math.min(
              prev.requiredSignatures,
              prev.collectedSignatures + 1,
            ),
            status:
              prev.collectedSignatures + 1 >= prev.requiredSignatures
                ? "ready_to_broadcast"
                : prev.status,
          }
        : prev,
    );
  };

  const handleBroadcast = () => {
    if (remoteProposal) {
      broadcastRemoteProposal(remoteProposal.id);
      return;
    }
    setLocalProposal((prev) =>
      prev
        ? {
            ...prev,
            status: "broadcast",
          }
        : prev,
    );
  };

  const walletLabel = useMemo(() => {
    if (walletLoading) return "Connecting...";
    if (address) return address;
    return "Connect Xaman Wallet";
  }, [address, walletLoading]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8 lg:flex-row">
        <div className="lg:w-1/3">
          <GroupList
            groups={groups}
            selectedGroupId={selectedGroupId}
            onSelect={setSelectedGroupId}
            onCreate={() => alert("Group creation TBD")}
            onJoin={() => alert("Join flow TBD")}
          />
        </div>
        <div className="flex-1 space-y-6">
          <div className="flex items-center justify-end">
            <button
              type="button"
              onClick={connect}
              className="rounded-full border border-xrpl-blue px-4 py-2 text-sm font-semibold text-white hover:bg-xrpl-blue/10"
            >
              {walletLabel}
            </button>
          </div>

          {group && (
            <GroupDashboard
              group={group}
              currentUser={address}
              onAddIou={handleAddIou}
              onProposeSettlement={handleProposeSettlement}
            >
              {activeProposal && (
                <SettlementProposal
                  proposal={activeProposal}
                  onSign={handleSign}
                  onBroadcast={handleBroadcast}
                />
              )}
            </GroupDashboard>
          )}
        </div>
      </div>
    </div>
  );
}

function buildPayments(members: Member[]): SettlementPayment[] {
  const debtors = members
    .filter((member) => member.netBalance > 0)
    .map((member) => ({ user: member.address, amount: member.netBalance }));
  const creditors = members
    .filter((member) => member.netBalance < 0)
    .map((member) => ({ user: member.address, amount: -member.netBalance }));

  const payments: SettlementPayment[] = [];
  let d = 0;
  let c = 0;

  while (d < debtors.length && c < creditors.length) {
    const debtor = debtors[d];
    const creditor = creditors[c];
    const amount = Math.min(debtor.amount, creditor.amount);

    payments.push({ from: debtor.user, to: creditor.user, amount });

    debtor.amount -= amount;
    creditor.amount -= amount;

    if (debtor.amount <= 0.0001) d += 1;
    if (creditor.amount <= 0.0001) c += 1;
  }

  return payments;
}
