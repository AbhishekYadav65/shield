import ResponsiveLayout from "../../layouts/ResponsiveLayout";
import { apiPost } from "../../api/client";
import { useState } from "react";

export default function ShiftControl() {
  const [uuid, setUuid] = useState("");

  return (
    <ResponsiveLayout title="Shift Control">
      <div className="max-w-sm space-y-3">
        <input
          className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
          placeholder="Worker UUID"
          onChange={(e) => setUuid(e.target.value)}
        />

        <button
          onClick={() => apiPost("/shift/start", { uuid })}
          className="w-full bg-primary text-white py-2 rounded-md text-sm"
        >
          Start Shift
        </button>

        <button
          onClick={() => apiPost("/shift/end", { uuid })}
          className="w-full border border-slate-300 py-2 rounded-md text-sm"
        >
          End Shift
        </button>
      </div>
    </ResponsiveLayout>
  );
}
