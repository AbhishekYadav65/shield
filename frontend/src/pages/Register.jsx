import { useState } from "react";
import { apiPost } from "../api/client";
import ResponsiveLayout from "../layouts/ResponsiveLayout";

export default function Register() {
  const [form, setForm] = useState({
    role: "worker",
    name: "",
    phone: "",
  });

  async function submit() {
    const res = await apiPost("/register", form);
    localStorage.setItem("uuid", res.uuid);
    localStorage.setItem("role", res.role);
    alert("Registered successfully");
  }

  return (
    <ResponsiveLayout title="Register">
      <div className="max-w-md space-y-4">
        <select
          className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
        >
          <option value="worker">Worker</option>
          <option value="customer">Customer</option>
        </select>

        <input
          className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />

        <input
          className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
          placeholder="Phone"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
        />

        <button
          onClick={submit}
          className="w-full bg-primary text-white py-2 rounded-md text-sm font-medium"
        >
          Register
        </button>
      </div>
    </ResponsiveLayout>
  );
}
