import { CalendarOff } from 'lucide-react';

export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <div className="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center">
        <CalendarOff size={22} className="text-gray-400" />
      </div>
      <div>
        <p className="text-sm font-semibold text-gray-700">No upcoming games</p>
        <p className="text-xs text-gray-400 mt-1">Check back later for new matchups.</p>
      </div>
    </div>
  );
}
