export default function ResponsiveLayout({ title, children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-6xl mx-auto px-6 py-6">
        <h1 className="text-xl font-semibold text-slate-900 mb-6">
          {title}
        </h1>

        <div className="bg-white border border-slate-200 rounded-lg p-6">
          {children}
        </div>
      </div>
    </div>
  );
}
