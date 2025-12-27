import ResponsiveLayout from "../../layouts/ResponsiveLayout";
import QRScanner from "../../components/QRScanner";
import { apiPost } from "../../api/client";
import { useState } from "react";

export default function PoliceHome() {
  const [result, setResult] = useState(null);

  async function scan(stt) {
    const res = await apiPost("/police/scan", { stt });
    setResult(res);
  }

  return (
    <ResponsiveLayout title="Police Verification">
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
    </ResponsiveLayout>
  );
}
