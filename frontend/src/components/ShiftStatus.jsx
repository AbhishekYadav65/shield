export default function ShiftStatus({ active }) {
  return (
    <div className="text-sm">
      <span className="font-medium text-slate-700">Shift:</span>{" "}
      <span
        className={`font-semibold ${
          active ? "text-green-600" : "text-slate-500"
        }`}
      >
        {active ? "ACTIVE" : "INACTIVE"}
      </span>
    </div>
  );
}
