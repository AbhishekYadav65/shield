import ResponsiveLayout from "../../layouts/ResponsiveLayout";
import { apiGet } from "../../api/client";
import usePoll from "../../hooks/usePoll";
import WorkerList from "../../components/WorkerList";

export default function SupervisorHome() {
  const data = usePoll(() => apiGet("/profile/supervisor"), 3000);

  return (
    <ResponsiveLayout title="Supervisor Dashboard">
      <WorkerList workers={data?.workers || []} />
    </ResponsiveLayout>
  );
}
