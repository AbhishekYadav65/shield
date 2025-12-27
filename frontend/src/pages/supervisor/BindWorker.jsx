import ResponsiveLayout from "../../layouts/ResponsiveLayout";
import { useState } from "react";
import { apiPost } from "../../api/client";

export default function BindWorker() {
  const [form, setForm] = useState({
    worker_uuid: "",
    workplace: "",
    location: "",
  });

  async function submit() {
    await apiPost("/workplace/bind", form);
    alert("Worker bound");
  }

  return (
    <ResponsiveLayout title="Bind Worker">
      <div className="max-w-md space-y-3">
        <input
          className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
          placeholder="Worker UUID"
          onChange={(e) =>
            setForm({ ...form, worker_uuid: e.target.value })
          }
        />

        <input
          className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
          placeholder="Workplace"
          onChange={(e) =>
            setForm({ ...form, workplace: e.target.value })
          }
        />

        <input
          className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
          placeholder="Location"
          onChange={(e) =>
            setForm({ ...form, location: e.target.value })
          }
        />

        <button
          onClick={submit}
          className="bg-primary text-white py-2 rounded-md text-sm font-medium"
        >
          Bind
        </button>
      </div>
    </ResponsiveLayout>
  );
}
