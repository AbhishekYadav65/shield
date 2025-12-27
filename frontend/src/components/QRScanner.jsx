import { useState } from "react";

export default function QRScanner({ onScan }) {
  const [value, setValue] = useState("");

  return (
    <div className="space-y-3">
      <input
        className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
        placeholder="Paste QR / STT value"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />

      <button
        onClick={() => onScan(value)}
        className="w-full bg-primary text-white py-2 rounded-md text-sm font-medium hover:opacity-90"
      >
        Scan
      </button>
    </div>
  );
}
