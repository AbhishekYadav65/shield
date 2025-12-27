import MobileLayout from "../../layouts/MobileLayout";
import { apiGet } from "../../api/client";
import { useEffect, useState } from "react";
import ProfileCard from "../../components/ProfileCard";

export default function WorkerProfile() {
  const uuid = localStorage.getItem("uuid");
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    apiGet(`/profile/${uuid}`).then(setProfile);
  }, []);

  return (
    <MobileLayout title="Worker Profile">
      {profile ? (
        <ProfileCard profile={profile} />
      ) : (
        <p className="text-sm text-slate-500">Loading...</p>
      )}
    </MobileLayout>
  );
}
