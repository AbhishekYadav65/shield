export default function WorkerList({ workers }) {
  if (!workers || workers.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        No workers found
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100 text-slate-700">
          <tr>
            <th className="px-3 py-2 text-left">UUID</th>
            <th className="px-3 py-2 text-left">Name</th>
            <th className="px-3 py-2 text-left">Role</th>
          </tr>
        </thead>
        <tbody>
          {workers.map((w) => (
            <tr
              key={w.uuid}
              className="border-t border-slate-200"
            >
              <td className="px-3 py-2">{w.uuid}</td>
              <td className="px-3 py-2">{w.name}</td>
              <td className="px-3 py-2">{w.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
