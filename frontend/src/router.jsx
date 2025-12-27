import { Routes, Route } from "react-router-dom";

import Landing from "./pages/Landing";
import Register from "./pages/Register";

import WorkerHome from "./pages/worker/WorkerHome";
import WorkerProfile from "./pages/worker/WorkerProfile";

import CustomerHome from "./pages/customer/CustomerHome";
import CustomerProfile from "./pages/customer/CustomerProfile";

import SupervisorHome from "./pages/supervisor/SupervisorHome";
import BindWorker from "./pages/supervisor/BindWorker";
import ShiftControl from "./pages/supervisor/ShiftControl";

import PoliceHome from "./pages/police/PoliceHome";

export default function Router() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/register" element={<Register />} />

      <Route path="/worker" element={<WorkerHome />} />
      <Route path="/worker/profile" element={<WorkerProfile />} />

      <Route path="/customer" element={<CustomerHome />} />
      <Route path="/customer/profile" element={<CustomerProfile />} />

      <Route path="/supervisor" element={<SupervisorHome />} />
      <Route path="/supervisor/bind" element={<BindWorker />} />
      <Route path="/supervisor/shift" element={<ShiftControl />} />

      <Route path="/police" element={<PoliceHome />} />
    </Routes>
  );
}
