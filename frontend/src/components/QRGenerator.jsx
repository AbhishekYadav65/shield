export default function QRGenerator({ value }) {
  return (
    <div className="border border-dashed border-slate-300 rounded-lg p-4 text-center bg-slate-50">
      <p className="text-xs text-slate-500 mb-2">SHIFT TRUST TOKEN</p>
      <code className="text-xs break-all text-slate-800">
        {value}
      </code>
    </div>
  );
}
