export default function MobileLayout({ title, children }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="w-full max-w-[390px] h-screen bg-white border border-slate-200 shadow-sm flex flex-col">
        {/* Header */}
        <header className="h-14 px-4 flex items-center border-b border-slate-200 bg-white sticky top-0 z-10">
          <h1 className="text-base font-semibold text-slate-900">
            {title}
          </h1>
        </header>

        {/* Body */}
        <main className="flex-1 overflow-y-auto p-4 space-y-4">
          {children}
        </main>
      </div>
    </div>
  );
}
