export default function EventLog({ events }) {
  if (!events || events.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        No events yet
      </p>
    );
  }

  return (
    <ul className="space-y-2 text-sm">
      {events.map((e, i) => (
        <li
          key={i}
          className="border border-slate-200 rounded-md px-3 py-2 bg-slate-50"
        >
          <span className="font-medium">{e.time}</span>{" "}
          <span className="text-slate-600">— {e.action}</span>
        </li>
      ))}
    </ul>
  );
}
