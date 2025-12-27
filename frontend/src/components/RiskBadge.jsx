export default function RiskBadge({ risk }) {
  const map = {
    green: "bg-green-600",
    yellow: "bg-amber-500",
    red: "bg-red-600",
  };

  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold text-white ${
        map[risk] || "bg-slate-400"
      }`}
    >
      {risk?.toUpperCase() || "UNKNOWN"}
    </span>
  );
}
