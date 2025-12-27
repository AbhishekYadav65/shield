import MobileLayout from "../../layouts/MobileLayout";
import QRScanner from "../../components/QRScanner";
import { apiPost } from "../../api/client";
import { useState } from "react";

export default function CustomerHome() {
  const uuid = localStorage.getItem("uuid");
  const [result, setResult] = useState(null);

  async function scan(stt) {
    const res = await apiPost("/verify/worker", {
      customer_uuid: uuid,
      stt,
    });
    setResult(res);
  }

  return (
    <MobileLayout title="Customer Verification">
      <div className="space-y-4">
        <QRScanner onScan={scan} />

        {result && (
          <div className="border border-slate-200 rounded-lg p-4 bg-white text-sm">
            <pre className="whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </MobileLayout>
  );
}
