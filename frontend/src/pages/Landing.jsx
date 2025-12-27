import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-6 space-y-4">
        <h1 className="text-xl font-semibold text-slate-900">
          TRUSTSHIFT
        </h1>

        <p className="text-sm text-slate-600">
          Real-time zero-trust workforce verification and shift-based
          authorization system.
        </p>

        <div className="space-y-2">
          <Link
          className="block w-full text-center border border-slate-300 py-2 rounded-md text-sm text-slate-900 hover:bg-slate-100"
          to="/register">
            Register
          </Link>


          <Link className="block w-full text-center border border-slate-300 py-2 rounded-md text-sm" to="/worker">
            Worker Dashboard
          </Link>

          <Link className="block w-full text-center border border-slate-300 py-2 rounded-md text-sm" to="/customer">
            Customer Dashboard
          </Link>

          <Link className="block w-full text-center border border-slate-300 py-2 rounded-md text-sm" to="/supervisor">
            Supervisor Dashboard
          </Link>

          <Link className="block w-full text-center border border-slate-300 py-2 rounded-md text-sm" to="/police">
            Police Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
