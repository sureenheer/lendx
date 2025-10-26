export type NetStatus = "settled" | "pending" | "broadcast" | "completed";
export type ProposalStatus =
  | "pending"
  | "pending_signatures"
  | "ready_to_broadcast"
  | "broadcast"
  | "completed";

export interface Member {
  address: string;
  displayName?: string;
  netBalance: number;
  lastActive: string;
  status: NetStatus;
  did?: string;
}

export interface GroupSummary {
  id: string;
  name: string;
  members: number;
  totalLocked: number;
}

export interface GroupDetails extends GroupSummary {
  depositAccount: string;
  memberDetails: Member[];
}

export interface IOURequest {
  debtor: string;
  creditor: string;
  amount: number;
}

export interface SettlementPayment {
  from: string;
  to: string;
  amount: number;
}

export interface SettlementProposalData {
  id: string;
  payments: SettlementPayment[];
  requiredSignatures: number;
  collectedSignatures: number;
  status: ProposalStatus;
}
