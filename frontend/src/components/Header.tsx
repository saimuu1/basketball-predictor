import { Activity } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-slate-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-3">
        <div className="flex items-center justify-center w-9 h-9 bg-blue-500 rounded-lg">
          <Activity size={20} className="text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold leading-tight tracking-tight">
            College Basketball Predictor
          </h1>
          <p className="text-xs text-slate-400 leading-none mt-0.5">
            Division I · AI-powered game predictions
          </p>
        </div>
        <div className="ml-auto">
          <span className="inline-flex items-center gap-1.5 bg-slate-800 border border-slate-700 text-slate-300 text-xs font-medium px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live
          </span>
        </div>
      </div>
    </header>
  );
}
