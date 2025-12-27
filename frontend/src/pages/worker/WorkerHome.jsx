import MobileLayout from "../../layouts/MobileLayout";
import { apiGet } from "../../api/client";
import usePoll from "../../hooks/usePoll";
import QRGenerator from "../../components/QRGenerator";
import RiskBadge from "../../components/RiskBadge";
import ShiftStatus from "../../components/ShiftStatus";

export default function WorkerHome() {
  const uuid = localStorage.getItem("uuid");

  const data = usePoll(
    () => apiGet(`/shift/status/${uuid}`),
    3000
  );

  if (!data) {
    return (
      <MobileLayout title="Worker">
        <p className="text-sm text-slate-500">Loading...</p>
      </MobileLayout>
    );
  }

  return (
    <MobileLayout title="Worker Dashboard">
      <div className="space-y-4">
        <div className="border border-slate-200 rounded-lg p-4 bg-white space-y-2">
          <h3 className="text-base font-semibold">{data.name}</h3>
          <ShiftStatus active={data.active} />
          <RiskBadge risk={data.risk_state} />
        </div>

        {data.active ? (
          <QRGenerator value={data.stt} />
        ) : (
          <p className="text-sm text-slate-500">
            Waiting for shift activation
          </p>
        )}
      </div>
    </MobileLayout>
  );
}
