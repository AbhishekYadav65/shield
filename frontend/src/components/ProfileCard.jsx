export default function ProfileCard({ profile }) {
  if (!profile) return null;

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white space-y-2">
      <h3 className="text-base font-semibold text-slate-900">
        {profile.name}
      </h3>

      <div className="text-sm text-slate-700">
        <p><span className="font-medium">Role:</span> {profile.role}</p>
        <p><span className="font-medium">UUID:</span> {profile.uuid}</p>

        <p>
          <span className="font-medium">Platforms:</span>{" "}
          {profile.platform_links?.length
            ? profile.platform_links.join(", ")
            : "None"}
        </p>

        <p>
          <span className="font-medium">Registered:</span>{" "}
          {profile.created_at}
        </p>
      </div>
    </div>
  );
}
